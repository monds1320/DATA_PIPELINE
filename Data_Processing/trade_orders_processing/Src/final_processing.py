import json
import boto3
import sys
from pathlib import Path
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, stddev, mean, least
from pyspark.sql.types import IntegerType, DoubleType

s3 = boto3.client('s3')
spark = SparkSession.builder.appName("FinalProcessing").getOrCreate()

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

def fix_data_types(df, issues):
    """Fix data type issues"""
    if not issues:
        return df, []
    
    fixes = []
    for issue in issues:
        if 'Expected numeric' in issue:
            col_name = issue.split("'")[1]
            if 'LongType' in issue or 'IntegerType' in issue:
                df = df.withColumn(col_name, col(col_name).cast(IntegerType()))
                fixes.append(f"Converted '{col_name}' to IntegerType")
            elif 'DoubleType' in issue or 'FloatType' in issue:
                df = df.withColumn(col_name, col(col_name).cast(DoubleType()))
                fixes.append(f"Converted '{col_name}' to DoubleType")
    
    return df, fixes

def fix_statistical_outliers(df, issues):
    """Fix statistical outliers by capping at 3 standard deviations"""
    if not issues:
        return df, []
    
    fixes = []
    for issue in issues:
        if 'statistical outliers' in issue:
            col_name = issue.split("'")[1]
            stats = df.select(mean(col(col_name)).alias('mean'), stddev(col(col_name)).alias('stddev')).collect()[0]
            
            if stats['stddev'] and stats['stddev'] > 0:
                lower_bound = stats['mean'] - 3 * stats['stddev']
                upper_bound = stats['mean'] + 3 * stats['stddev']
                
                df = df.withColumn(col_name,
                    when(col(col_name) < lower_bound, lower_bound)
                    .when(col(col_name) > upper_bound, upper_bound)
                    .otherwise(col(col_name))
                )
                fixes.append(f"Capped outliers in '{col_name}' at ±3σ (mean={stats['mean']:.2f}, std={stats['stddev']:.2f})")
    
    return df, fixes

def fix_referential_integrity(df, issues):
    """Fix referential integrity issues"""
    if not issues:
        return df, []
    
    fixes = []
    for issue in issues:
        if 'executed_quantity > quantity' in issue:
            # Cap executed_quantity to quantity
            df = df.withColumn('executed_quantity', least(col('executed_quantity'), col('quantity')))
            fixes.append(f"Fixed executed_quantity to not exceed quantity")
        
        if 'price variance' in issue:
            # Cap execution_price variance to ±5%
            df = df.withColumn('execution_price',
                when(col('execution_price') > col('order_price') * 1.05, col('order_price') * 1.05)
                .when(col('execution_price') < col('order_price') * 0.95, col('order_price') * 0.95)
                .otherwise(col('execution_price'))
            )
            fixes.append(f"Capped execution_price variance to ±5% of order_price")
    
    return df, fixes

def run_final_processing(quality_report_path, input_data_path, s3_output_path, local_output_dir):
    print(f"Reading quality check report from {quality_report_path}...")
    quality_report = read_json_from_s3(quality_report_path)
    
    print(f"Quality Score: {quality_report['qualityScore']}")
    print(f"Checks Failed: {quality_report['checksFailed']}")
    
    print(f"\nReading input data from {input_data_path}...")
    data = read_json_from_s3(input_data_path)
    df = spark.createDataFrame(data)
    
    original_count = df.count()
    all_fixes = []
    
    # Fix issues based on quality report
    checks = quality_report.get('checks', {})
    
    if checks.get('Data Types', {}).get('status') == 'FAIL':
        print("\nFixing Data Types...")
        issues = checks['Data Types']['issues']
        df, fixes = fix_data_types(df, issues)
        all_fixes.extend(fixes)
    
    if checks.get('Statistical Outliers', {}).get('status') == 'FAIL':
        print("Fixing Statistical Outliers...")
        issues = checks['Statistical Outliers']['issues']
        df, fixes = fix_statistical_outliers(df, issues)
        all_fixes.extend(fixes)
    
    if checks.get('Referential Integrity', {}).get('status') == 'FAIL':
        print("Fixing Referential Integrity...")
        issues = checks['Referential Integrity']['issues']
        df, fixes = fix_referential_integrity(df, issues)
        all_fixes.extend(fixes)
    
    final_data = [row.asDict() for row in df.collect()]
    final_count = len(final_data)
    
    # Create processing report
    processing_report = {
        'originalQualityScore': quality_report['qualityScore'],
        'totalRecords': final_count,
        'fixesApplied': len(all_fixes),
        'fixes': all_fixes,
        'status': 'COMPLETED'
    }
    
    # Save final data to S3
    data_s3 = s3_output_path.rstrip('/') + '/final_processed_data.json'
    print(f"\nWriting final data to {data_s3}...")
    write_json_to_s3(data_s3, final_data)
    
    # Save final data locally
    data_local = Path(local_output_dir) / "final_processed_data.json"
    print(f"Writing final data to {data_local}...")
    write_json_to_local(data_local, final_data)
    
    # Save processing report to S3
    report_s3 = s3_output_path.rstrip('/') + '/final_processing_report.json'
    print(f"Writing processing report to {report_s3}...")
    write_json_to_s3(report_s3, processing_report)
    
    # Save processing report locally
    report_local = Path(local_output_dir) / "final_processing_report.json"
    print(f"Writing processing report to {report_local}...")
    write_json_to_local(report_local, processing_report)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"FINAL PROCESSING REPORT")
    print(f"{'='*60}")
    print(f"Original Quality Score: {quality_report['qualityScore']}")
    print(f"Records Processed: {final_count}")
    print(f"Fixes Applied: {len(all_fixes)}")
    print(f"\nFixes:")
    for fix in all_fixes:
        print(f"  ✓ {fix}")
    print(f"{'='*60}")
    print(f"\nOutputs saved to:")
    print(f"  Data S3: {data_s3}")
    print(f"  Data Local: {data_local}")
    print(f"  Report S3: {report_s3}")
    print(f"  Report Local: {report_local}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python final_processing.py <quality_report_s3> <input_data_s3> <s3_output_path> <local_output_dir>")
        print("Example: python final_processing.py s3://bucket/report.json s3://bucket/data.json s3://bucket/output/ /path/to/local/")
        sys.exit(1)
    
    quality_report_path = sys.argv[1]
    input_data_path = sys.argv[2]
    s3_output = sys.argv[3]
    local_output = sys.argv[4]
    
    run_final_processing(quality_report_path, input_data_path, s3_output, local_output)
