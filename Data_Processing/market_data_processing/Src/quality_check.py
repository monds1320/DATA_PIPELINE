import json
import boto3
import sys
from pathlib import Path
from datetime import datetime

s3 = boto3.client('s3')

def read_json_from_s3(s3_path):
    bucket = s3_path.split('/')[2]
    key = '/'.join(s3_path.split('/')[3:])
    obj = s3.get_object(Bucket=bucket, Key=key)
    return json.loads(obj['Body'].read().decode('utf-8'))

def write_json_to_s3(s3_path, data):
    bucket = s3_path.split('/')[2]
    key = '/'.join(s3_path.split('/')[3:])
    s3.put_object(Bucket=bucket, Key=key, Body=json.dumps(data, indent=2))

def write_json_to_local(local_path, data):
    Path(local_path).parent.mkdir(parents=True, exist_ok=True)
    with open(local_path, 'w') as f:
        json.dump(data, f, indent=2)

def check_completeness(data):
    """Check for missing values"""
    total_rows = len(data)
    null_counts = {}
    
    for col in data[0].keys():
        null_counts[col] = sum(1 for row in data if not row.get(col) or row.get(col) == '')
    
    issues = [f"Column '{col}': {cnt} nulls ({cnt/total_rows*100:.1f}%)" 
              for col, cnt in null_counts.items() if cnt > 0]
    return len(issues) == 0, issues[:5]

def check_data_types(data):
    """Validate data types - dynamically detect numeric columns"""
    issues = []
    
    # Dynamically detect columns that should be numeric
    for col in data[0].keys():
        # Skip known string columns
        if any(keyword in col.lower() for keyword in ['symbol', 'ticker', 'name', 'status', 'type', 'category', 'day_of_week']):
            continue
        
        # Check if column looks numeric
        for row in data[:100]:
            try:
                float(row.get(col, 0))
            except:
                issues.append(f"Invalid numeric value in '{col}': {row.get(col)}")
                break
        if len(issues) >= 5:
            break
    
    return len(issues) == 0, issues

def check_business_rules(data):
    """Validate stock market business logic - dynamically find price columns"""
    issues = []
    
    # Dynamically find price columns
    sample_row = data[0] if data else {}
    high_col = next((col for col in sample_row.keys() if 'high' in col.lower()), None)
    low_col = next((col for col in sample_row.keys() if 'low' in col.lower()), None)
    close_col = next((col for col in sample_row.keys() if 'close' in col.lower()), None)
    volume_cols = [col for col in sample_row.keys() if 'volume' in col.lower()]
    price_cols = [col for col in sample_row.keys() if any(kw in col.lower() for kw in ['open', 'high', 'low', 'close', 'price'])]
    
    for i, row in enumerate(data[:1000]):
        # Check if high >= low
        if high_col and low_col:
            try:
                high = float(row.get(high_col, 0))
                low = float(row.get(low_col, 0))
                if high < low:
                    issues.append(f"Row {i}: {high_col} ({high}) < {low_col} ({low})")
            except:
                pass
        
        # Check if close is between high and low
        if close_col and high_col and low_col:
            try:
                close = float(row.get(close_col, 0))
                high = float(row.get(high_col, 0))
                low = float(row.get(low_col, 0))
                if not (low <= close <= high):
                    issues.append(f"Row {i}: {close_col} ({close}) not between {high_col} ({high}) and {low_col} ({low})")
            except:
                pass
        
        # Check for negative prices
        for col in price_cols:
            try:
                val = float(row.get(col, 0))
                if val < 0:
                    issues.append(f"Row {i}: Negative {col} price: {val}")
            except:
                pass
        
        # Check for negative volume
        for vol_col in volume_cols:
            try:
                vol = int(float(row.get(vol_col, 0)))
                if vol < 0:
                    issues.append(f"Row {i}: Negative {vol_col}: {vol}")
            except:
                pass
        
        if len(issues) >= 10:
            break
    
    return len(issues) == 0, issues[:5]

def check_duplicates(data):
    """Check for duplicate records - dynamically find key columns"""
    seen = set()
    duplicates = 0
    
    # Dynamically find key columns
    sample_row = data[0] if data else {}
    key_cols = []
    for col in sample_row.keys():
        if any(keyword in col.lower() for keyword in ['symbol', 'ticker', 'stock', 'id']):
            key_cols.append(col)
        elif any(keyword in col.lower() for keyword in ['date', 'time', 'timestamp']):
            key_cols.append(col)
    
    if not key_cols:
        # If no key columns, use all columns
        key_cols = list(sample_row.keys())
    
    for row in data:
        key = tuple(row.get(col) for col in key_cols)
        if key in seen:
            duplicates += 1
        seen.add(key)
    
    return duplicates == 0, [f"Found {duplicates} duplicate records (based on {', '.join(key_cols)})"] if duplicates > 0 else []

def check_consistency(data):
    """Check data consistency - dynamically find symbol and date columns"""
    issues = []
    
    # Dynamically find symbol columns
    sample_row = data[0] if data else {}
    symbol_cols = [col for col in sample_row.keys() if any(kw in col.lower() for kw in ['symbol', 'ticker', 'stock'])]
    
    # Check valid symbols
    if symbol_cols:
        symbols = set(row.get(symbol_cols[0]) for row in data)
        if len(symbols) == 0:
            issues.append(f"No {symbol_cols[0]} found in data")
    
    # Dynamically find date columns
    date_cols = [col for col in sample_row.keys() if 'date' in col.lower() or 'time' in col.lower()]
    
    # Check date format
    if date_cols:
        invalid_dates = 0
        for row in data[:100]:
            date_str = row.get(date_cols[0], '')
            try:
                datetime.strptime(date_str, '%Y-%m-%d')
            except:
                invalid_dates += 1
        
        if invalid_dates > 0:
            issues.append(f"Found {invalid_dates} records with invalid {date_cols[0]} format")
    
    return len(issues) == 0, issues

def check_statistical_outliers(data):
    """Detect statistical outliers - dynamically find numeric columns"""
    issues = []
    
    # Dynamically detect numeric columns
    sample_row = data[0] if data else {}
    numeric_cols = []
    
    for col in sample_row.keys():
        # Skip known string columns
        if any(keyword in col.lower() for keyword in ['symbol', 'ticker', 'name', 'status', 'type', 'category', 'day_of_week']):
            continue
        # Try to convert sample values
        try:
            sample_vals = [float(row.get(col, 0)) for row in data[:10]]
            if sample_vals:
                numeric_cols.append(col)
        except:
            pass
    
    for col in numeric_cols:
        values = []
        for row in data:
            try:
                values.append(float(row.get(col, 0)))
            except:
                pass
        
        if values:
            mean = sum(values) / len(values)
            variance = sum((x - mean)**2 for x in values) / len(values)
            stddev = variance**0.5
            
            outliers = sum(1 for v in values if abs(v - mean) > 3 * stddev)
            if outliers > 0:
                issues.append(f"Column '{col}': {outliers} statistical outliers (Z-score > 3)")
    
    return len(issues) == 0, issues

def check_data_distribution(data):
    """Analyze data distribution - dynamically find grouping columns"""
    issues = []
    
    # Dynamically find columns to check distribution
    sample_row = data[0] if data else {}
    group_cols = [col for col in sample_row.keys() if any(kw in col.lower() 
                  for kw in ['symbol', 'ticker', 'status', 'type', 'category'])]
    
    total = len(data)
    
    for col in group_cols:
        col_counts = {}
        for row in data:
            val = row.get(col)
            col_counts[val] = col_counts.get(val, 0) + 1
        
        for val, count in col_counts.items():
            pct = (count / total) * 100
            if pct > 80:
                issues.append(f"Skewed distribution: {col}={val} represents {pct:.1f}% of data")
    
    return len(issues) == 0, issues

def run_quality_check(input_data_path, s3_output_path, local_output_dir):
    print(f"Reading data from {input_data_path}...")
    data = read_json_from_s3(input_data_path)
    
    total_records = len(data)
    print(f"Total records: {total_records}")
    
    print("\nRunning quality checks...")
    
    checks = {
        'Completeness': check_completeness(data),
        'Data Types': check_data_types(data),
        'Business Rules': check_business_rules(data),
        'Duplicates': check_duplicates(data),
        'Consistency': check_consistency(data),
        'Statistical Outliers': check_statistical_outliers(data),
        'Data Distribution': check_data_distribution(data)
    }
    
    passed = sum(1 for status, _ in checks.values() if status)
    total = len(checks)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'totalRecords': total_records,
        'qualityScore': f"{(passed/total)*100:.1f}%",
        'checksPerformed': total,
        'checksPassed': passed,
        'checksFailed': total - passed,
        'checks': {}
    }
    
    for check_name, (status, issues) in checks.items():
        report['checks'][check_name] = {
            'status': 'PASS' if status else 'FAIL',
            'issues': issues if not status else []
        }
    
    report_s3 = s3_output_path.rstrip('/') + '/quality_check_report.json'
    print(f"\nWriting report to {report_s3}...")
    write_json_to_s3(report_s3, report)
    
    local_path = Path(local_output_dir) / "quality_check_report.json"
    print(f"Writing report to {local_path}...")
    write_json_to_local(local_path, report)
    
    print(f"\n{'='*60}")
    print(f"QUALITY CHECK REPORT")
    print(f"{'='*60}")
    print(f"Total Records: {total_records}")
    print(f"Quality Score: {report['qualityScore']}")
    print(f"Checks Passed: {passed}/{total}")
    print(f"\nCheck Results:")
    for check_name, result in report['checks'].items():
        status_icon = '✓' if result['status'] == 'PASS' else '✗'
        print(f"  {status_icon} {check_name}: {result['status']}")
        if result['issues']:
            for issue in result['issues'][:3]:
                print(f"      - {issue}")
    print(f"{'='*60}")
    print(f"\nReport saved to:")
    print(f"  S3: {report_s3}")
    print(f"  Local: {local_path}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python quality_check.py <input_data_s3> <s3_output_path> <local_output_dir>")
        sys.exit(1)
    
    input_data_path = sys.argv[1]
    s3_output = sys.argv[2]
    local_output = sys.argv[3]
    
    run_quality_check(input_data_path, s3_output, local_output)
