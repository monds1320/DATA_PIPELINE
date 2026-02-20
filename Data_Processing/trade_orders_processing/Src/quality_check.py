import json
import boto3
import sys
from pathlib import Path
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, isnan, isnull, when, stddev, mean, min as spark_min, max as spark_max
import numpy as np

s3 = boto3.client('s3')
spark = SparkSession.builder.appName("QualityCheck").getOrCreate()

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

def check_completeness(df):
    """Check for missing values using PySpark"""
    total_rows = df.count()
    null_counts = df.select([count(when(col(c).isNull() | isnan(c), c)).alias(c) for c in df.columns]).collect()[0].asDict()
    issues = [f"Column '{col}': {cnt} nulls ({cnt/total_rows*100:.1f}%)" for col, cnt in null_counts.items() if cnt > 0]
    return len(issues) == 0, issues[:5]

def check_data_types(df):
    """Validate data types using schema"""
    issues = []
    expected_numeric = ['quantity', 'order_price', 'execution_price', 'executed_quantity', 'volume']
    for field in df.schema.fields:
        if field.name in expected_numeric and str(field.dataType) not in ['IntegerType', 'DoubleType', 'LongType', 'FloatType']:
            issues.append(f"Column '{field.name}': Expected numeric, got {field.dataType}")
    return len(issues) == 0, issues

def check_business_rules(df):
    """Validate business logic using PySpark"""
    issues = []
    neg_qty = df.filter(col('quantity') < 0).count()
    if neg_qty > 0:
        issues.append(f"Found {neg_qty} records with negative quantity")
    
    invalid_price = df.filter(col('order_price') <= 0).count()
    if invalid_price > 0:
        issues.append(f"Found {invalid_price} records with invalid order_price")
    
    neg_exec_price = df.filter(col('execution_price') < 0).count()
    if neg_exec_price > 0:
        issues.append(f"Found {neg_exec_price} records with negative execution_price")
    
    return len(issues) == 0, issues

def check_duplicates(df):
    """Check for duplicate records using PySpark"""
    total = df.count()
    distinct = df.distinct().count()
    duplicates = total - distinct
    return duplicates == 0, [f"Found {duplicates} duplicate records"] if duplicates > 0 else []

def check_consistency(df):
    """Check data consistency using PySpark"""
    issues = []
    valid_statuses = ['FILLED', 'PARTIAL', 'CANCELLED', 'PENDING']
    invalid_status = df.filter(~col('order_status').isin(valid_statuses)).count()
    if invalid_status > 0:
        issues.append(f"Found {invalid_status} records with invalid order_status")
    
    valid_types = ['LIMIT', 'MARKET', 'STOP']
    invalid_type = df.filter(~col('order_type').isin(valid_types)).count()
    if invalid_type > 0:
        issues.append(f"Found {invalid_type} records with invalid order_type")
    
    return len(issues) == 0, issues

def check_statistical_outliers(df):
    """Detect statistical outliers using Z-score method"""
    issues = []
    numeric_cols = ['quantity', 'order_price', 'execution_price', 'executed_quantity', 'volume']
    
    for col_name in numeric_cols:
        if col_name in df.columns:
            stats = df.select(mean(col(col_name)).alias('mean'), stddev(col(col_name)).alias('stddev')).collect()[0]
            if stats['stddev'] and stats['stddev'] > 0:
                outliers = df.filter(
                    (col(col_name) < stats['mean'] - 3 * stats['stddev']) |
                    (col(col_name) > stats['mean'] + 3 * stats['stddev'])
                ).count()
                if outliers > 0:
                    issues.append(f"Column '{col_name}': {outliers} statistical outliers (Z-score > 3)")
    
    return len(issues) == 0, issues

def check_referential_integrity(df):
    """Check referential integrity and relationships"""
    issues = []
    
    # Check if executed_quantity <= quantity for non-cancelled orders
    invalid_exec = df.filter(
        (col('order_status') != 'CANCELLED') & 
        (col('executed_quantity') > col('quantity'))
    ).count()
    if invalid_exec > 0:
        issues.append(f"Found {invalid_exec} records where executed_quantity > quantity")
    
    # Check price variance
    price_variance = df.filter(
        ((col('execution_price') - col('order_price')) / col('order_price') * 100).cast('double') > 5
    ).count()
    if price_variance > 0:
        issues.append(f"Found {price_variance} records with >5% price variance")
    
    return len(issues) == 0, issues

def check_data_distribution(df):
    """Analyze data distribution"""
    issues = []
    
    # Check for skewed distributions
    status_dist = df.groupBy('order_status').count().collect()
    total = df.count()
    for row in status_dist:
        pct = (row['count'] / total) * 100
        if pct > 80:
            issues.append(f"Skewed distribution: {row['order_status']} represents {pct:.1f}% of data")
    
    return len(issues) == 0, issues

def run_quality_check(input_data_path, s3_output_path, local_output_dir):
    print(f"Reading data from {input_data_path}...")
    data = read_json_from_s3(input_data_path)
    df = spark.createDataFrame(data)
    
    total_records = df.count()
    print(f"Total records: {total_records}")
    
    # Run quality checks
    print("\nRunning advanced quality checks...")
    
    checks = {
        'Completeness': check_completeness(df),
        'Data Types': check_data_types(df),
        'Business Rules': check_business_rules(df),
        'Duplicates': check_duplicates(df),
        'Consistency': check_consistency(df),
        'Statistical Outliers': check_statistical_outliers(df),
        'Referential Integrity': check_referential_integrity(df),
        'Data Distribution': check_data_distribution(df)
    }
    
    # Generate report
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
    
    # Save report to S3
    report_s3 = s3_output_path.rstrip('/') + '/quality_check_report.json'
    print(f"\nWriting report to {report_s3}...")
    write_json_to_s3(report_s3, report)
    
    # Save report locally
    local_path = Path(local_output_dir) / "quality_check_report.json"
    print(f"Writing report to {local_path}...")
    write_json_to_local(local_path, report)
    
    # Print summary
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
        print("Example: python quality_check.py s3://bucket/data.json s3://bucket/output/ /path/to/local/")
        sys.exit(1)
    
    input_data_path = sys.argv[1]
    s3_output = sys.argv[2]
    local_output = sys.argv[3]
    
    run_quality_check(input_data_path, s3_output, local_output)
