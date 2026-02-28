import json
import boto3
import sys
import csv
from datetime import datetime
from pathlib import Path
from io import StringIO

s3 = boto3.client('s3')

def read_csv_from_s3(s3_path):
    bucket = s3_path.split('/')[2]
    key = '/'.join(s3_path.split('/')[3:])
    obj = s3.get_object(Bucket=bucket, Key=key)
    csv_string = obj['Body'].read().decode('utf-8')
    reader = csv.DictReader(StringIO(csv_string))
    return list(reader)

def get_data_type(value):
    if value is None or value == '':
        return "null"
    try:
        int(value)
        return "IntegerType()"
    except:
        pass
    try:
        float(value)
        return "DoubleType()"
    except:
        pass
    return "StringType()"

def detect_pii_columns(columns, data):
    pii_keywords = ['id', 'name', 'email', 'phone', 'address', 'ssn', 'account', 'trader', 'customer', 'user']
    pii_cols = []
    for col in columns:
        if any(kw in col.lower() for kw in pii_keywords):
            pii_cols.append(col)
    return pii_cols

def profile_data(data, source_path, file_format):
    if not data:
        return None
    
    row_count = len(data)
    columns = list(data[0].keys()) if isinstance(data[0], dict) else []
    column_count = len(columns)
    
    # Schema detection
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
        null_counts[col] = sum(1 for row in data if not row.get(col) or row.get(col) == '')
    
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
    
    # Numeric stats
    numeric_stats = {}
    for col in columns:
        values = []
        for row in data:
            try:
                val = float(row.get(col, ''))
                values.append(val)
            except:
                pass
        
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
    
    # Recommendations
    recommendations = [
        {"priority": 1, "process": "DATA_PROFILING", "reason": "Completed - See detailed metrics above", "required": True}
    ]
    
    recommendations.append({
        "priority": 2,
        "process": "DEDUPLICATION",
        "reason": f"Found {duplicate_count} duplicate records",
        "required": duplicate_count > 0
    })
    
    recommendations.append({
        "priority": 3,
        "process": "ETL_TRANSFORM",
        "reason": "Transform required: clean data, create derived columns, and aggregate metrics",
        "required": True
    })
    
    recommendations.append({
        "priority": 4,
        "process": "PII_MASKING",
        "reason": f"Found {len(pii_columns)} PII columns: {pii_columns}" if pii_columns else "No PII detected - masking step will be skipped",
        "required": len(pii_columns) > 0
    })
    
    recommendations.append({
        "priority": 5,
        "process": "QUALITY_CHECK",
        "reason": "Validate data quality and business rules",
        "required": True
    })
    
    recommendations.append({
        "priority": 6,
        "process": "FINAL_PROCESSING",
        "reason": "Store processed data in partitioned format",
        "required": True
    })
    
    profile_id = "MarketData_Profile_001"
    
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
        sys.exit(1)
    
    s3_input = sys.argv[1]
    s3_output = sys.argv[2]
    
    file_format = "csv"
    
    print(f"Reading CSV data from {s3_input}...")
    data = read_csv_from_s3(s3_input)
    
    print(f"Profiling {len(data)} records...")
    profile = profile_data(data, s3_input, file_format)
    
    print(f"Writing report to {s3_output}...")
    write_to_s3(s3_output, profile)
    
    local_output = Path(__file__).parent.parent / "outputs" / "report.json"
    print(f"Writing report to {local_output}...")
    write_to_local(local_output, profile)
    
    print(f"✓ Profiling complete!")
    print(f"  S3: {s3_output}")
    print(f"  Local: {local_output}")
