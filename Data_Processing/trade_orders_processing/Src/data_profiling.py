import json
import boto3
import sys
from datetime import datetime
from pathlib import Path

s3 = boto3.client('s3')

def read_from_s3(s3_path):
    bucket = s3_path.split('/')[2]
    key = '/'.join(s3_path.split('/')[3:])
    obj = s3.get_object(Bucket=bucket, Key=key)
    return json.loads(obj['Body'].read().decode('utf-8'))

def get_data_type(value):
    if value is None:
        return "null"
    elif isinstance(value, bool):
        return "BooleanType()"
    elif isinstance(value, int):
        return "IntegerType()"
    elif isinstance(value, float):
        return "DoubleType()"
    elif isinstance(value, str):
        return "StringType()"
    elif isinstance(value, list):
        return "ArrayType(StringType(), True)"
    return "StringType()"

def detect_pii_columns(columns, data):
    pii_keywords = ['id', 'name', 'email', 'phone', 'address', 'ssn', 'account', 'trader', 'customer', 'user', 'patient', 'person']
    pii_cols = []
    for col in columns:
        if any(kw in col.lower() for kw in pii_keywords):
            pii_cols.append(col)
        else:
            sample_vals = [str(row.get(col, '')) for row in data[:100] if row.get(col)]
            if sample_vals and any(len(str(v)) > 20 and any(c.isalpha() for c in str(v)) for v in sample_vals[:10]):
                pii_cols.append(col)
    return pii_cols

def profile_data(data, source_path, file_format):
    if not data:
        return None
    
    row_count = len(data)
    columns = list(data[0].keys()) if isinstance(data[0], dict) else []
    column_count = len(columns)
    
    # Schema detection - check multiple rows for accurate type inference
    schema = {}
    for col in columns:
        type_counts = {}
        for row in data[:min(100, len(data))]:
            val = row.get(col)
            dtype = get_data_type(val)
            type_counts[dtype] = type_counts.get(dtype, 0) + 1
        schema[col] = max(type_counts, key=type_counts.get) if type_counts else "StringType()"
    
    # Null counts
    null_counts = {}
    for col in columns:
        null_counts[col] = sum(1 for row in data if row.get(col) is None or row.get(col) == "" or (isinstance(row.get(col), float) and str(row.get(col)) == 'nan'))
    
    # Duplicate detection
    unique_rows = set()
    for row in data:
        try:
            unique_rows.add(json.dumps(row, sort_keys=True))
        except:
            pass
    duplicate_count = row_count - len(unique_rows)
    
    # PII detection
    pii_columns = detect_pii_columns(columns, data)
    
    # Numeric stats - only for numeric columns
    numeric_stats = {}
    for col in columns:
        values = [row[col] for row in data if row.get(col) is not None and isinstance(row.get(col), (int, float)) and str(row.get(col)) != 'nan']
        if values:
            avg = sum(values) / len(values)
            variance = sum((x - avg)**2 for x in values) / len(values)
            numeric_stats[col] = {
                "min": str(min(values)),
                "max": str(max(values)),
                "avg": str(avg),
                "stddev": str(variance**0.5)
            }
        else:
            numeric_stats[col] = {"min": None, "max": None, "avg": None, "stddev": None}
    
    # Dynamic recommendations with ETL detection
    recommendations = [
        {"priority": 1, "process": "DATA_PROFILING", "reason": "Completed - See detailed metrics above", "required": True}
    ]
    
    # Separate deduplication check - always show
    recommendations.append({
        "priority": len(recommendations) + 1,
        "process": "DEDUPLICATION",
        "reason": f"Found {duplicate_count} duplicate records" + (f" ({duplicate_count/row_count*100:.2f}%)" if duplicate_count > 0 else ""),
        "required": duplicate_count > 0
    })
    
    # Detect if ETL Clean is needed
    null_col_count = sum(1 for v in null_counts.values() if v > 0)
    type_issues = sum(1 for col, dtype in schema.items() if dtype == "null")
    
    if null_col_count > 0 or type_issues > 0:
        clean_reasons = []
        if null_col_count > 0:
            clean_reasons.append(f"handle missing values in {null_col_count} columns")
        if type_issues > 0:
            clean_reasons.append(f"fix data types in {type_issues} columns")
        
        recommendations.append({
            "priority": len(recommendations) + 1,
            "process": "ETL_CLEAN",
            "reason": f"Clean required: {', '.join(clean_reasons)}",
            "required": True
        })
    
    # Detect if ETL Transform is needed
    transform_needed = False
    transform_reasons = []
    
    # Check if filtering needed (outliers, invalid records)
    for col in columns:
        values = [row[col] for row in data if row.get(col) is not None and isinstance(row.get(col), (int, float))]
        if values and len(values) > 10:
            avg = sum(values) / len(values)
            stddev = (sum((x - avg)**2 for x in values) / len(values))**0.5
            outliers = sum(1 for v in values if abs(v - avg) > 3 * stddev)
            if outliers > 0:
                transform_needed = True
                transform_reasons.append(f"filter {outliers} outliers")
                break
    
    # Check if aggregation needed (multiple records per key)
    if len(columns) > 5:
        transform_needed = True
        transform_reasons.append("aggregate metrics by key dimensions")
    
    # Check if derived columns needed
    date_cols = [col for col in columns if 'date' in col.lower() or 'time' in col.lower()]
    if date_cols:
        transform_needed = True
        transform_reasons.append("create derived time-based columns")
    
    if transform_needed:
        recommendations.append({
            "priority": len(recommendations) + 1,
            "process": "ETL_TRANSFORM",
            "reason": f"Transform required: {', '.join(transform_reasons)}",
            "required": True
        })
    
    if pii_columns:
        recommendations.append({
            "priority": len(recommendations) + 1,
            "process": "PII_MASKING",
            "reason": f"Found {len(pii_columns)} PII columns: {pii_columns}",
            "required": True
        })
    
    recommendations.append({
        "priority": len(recommendations) + 1,
        "process": "QUALITY_CHECK",
        "reason": "Validate data quality and business rules",
        "required": True
    })
    
    recommendations.append({
        "priority": len(recommendations) + 1,
        "process": "FINAL_PROCESSING",
        "reason": "Store processed data in partitioned format",
        "required": True
    })
    
    profile_id = Path(source_path).stem.replace('_', '').title() + "_Profile_001"
    
    return {
        "profileId": profile_id,
        "timestamp": datetime.now().isoformat(),
        "source": {"path": source_path, "format": file_format},
        "dataProfile": {
            "rowCount": row_count,
            "columnCount": column_count,
            "columns": columns,
            "schema": schema,
            "nullCounts": null_counts,
            "duplicateCount": duplicate_count,
            "piiColumns": pii_columns,
            "numericStats": numeric_stats
        },
        "recommendations": recommendations
    }

def write_to_s3(s3_path, data):
    bucket = s3_path.split('/')[2]
    key = '/'.join(s3_path.split('/')[3:])
    s3.put_object(Bucket=bucket, Key=key, Body=json.dumps(data, indent=2))

def write_to_local(local_path, data):
    Path(local_path).parent.mkdir(parents=True, exist_ok=True)
    with open(local_path, 'w') as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python data_profiling.py <s3_input_path> <s3_output_path>")
        print("Example: python data_profiling.py s3://bucket/input.json s3://bucket/output.json")
        sys.exit(1)
    
    s3_input = sys.argv[1]
    s3_output = sys.argv[2]
    
    file_format = Path(s3_input).suffix[1:] if Path(s3_input).suffix else "json"
    
    print(f"Reading data from {s3_input}...")
    data = read_from_s3(s3_input)
    
    print(f"Profiling {len(data)} records...")
    profile = profile_data(data, s3_input, file_format)
    
    print(f"Writing report to {s3_output}...")
    write_to_s3(s3_output, profile)
    
    # Also save locally
    local_output = Path(__file__).parent / "outputs" / "report.json"
    print(f"Writing report to {local_output}...")
    write_to_local(local_output, profile)
    
    print(f"✓ Profiling complete!")
    print(f"  S3: {s3_output}")
    print(f"  Local: {local_output}")
