import json
import boto3
import sys
from pathlib import Path
from pyspark.sql import SparkSession, Window
from pyspark.sql.functions import (
    col, when, lit, round as spark_round, trim, upper, lower,
    regexp_replace, coalesce, avg, sum as spark_sum, count, min as spark_min, max as spark_max,
    stddev, variance, percentile_approx, row_number, dense_rank, lag, lead
)
from pyspark.sql.types import IntegerType, DoubleType, StringType, TimestampType, LongType

s3 = boto3.client('s3')
spark = SparkSession.builder.appName("ETL").getOrCreate()

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

def etl_clean(df, profile):
    """Clean: Handle missing values, fix data types, remove outliers, standardize strings"""
    schema = profile.get('dataProfile', {}).get('schema', [])
    numeric_stats = profile.get('dataProfile', {}).get('numericStats', {})
    
    # Handle missing values
    for field in schema:
        col_name = field['name']
        data_type = field['type']
        null_count = field.get('nullCount', 0)
        
        if null_count > 0:
            if data_type in ['IntegerType', 'DoubleType', 'LongType']:
                # Fill with median for numeric
                stats = numeric_stats.get(col_name, {})
                fill_value = stats.get('median', stats.get('mean', 0))
                df = df.fillna({col_name: fill_value})
            else:
                # Fill with mode or UNKNOWN for strings
                df = df.fillna({col_name: 'UNKNOWN'})
        
        # Fix data types
        if data_type == 'IntegerType':
            df = df.withColumn(col_name, col(col_name).cast(IntegerType()))
        elif data_type == 'DoubleType':
            df = df.withColumn(col_name, col(col_name).cast(DoubleType()))
        elif data_type == 'LongType':
            df = df.withColumn(col_name, col(col_name).cast(LongType()))
        elif data_type == 'StringType':
            # Standardize strings: trim, handle nulls
            df = df.withColumn(col_name, trim(col(col_name)))
            df = df.withColumn(col_name, when(col(col_name) == '', None).otherwise(col(col_name)))
    
    # Remove outliers for numeric columns using IQR method
    for col_name, stats in numeric_stats.items():
        if col_name in df.columns and stats.get('q1') and stats.get('q3'):
            q1 = stats['q1']
            q3 = stats['q3']
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            # Cap outliers instead of removing
            df = df.withColumn(col_name, 
                when(col(col_name) < lower_bound, lit(lower_bound))
                .when(col(col_name) > upper_bound, lit(upper_bound))
                .otherwise(col(col_name))
            )
    
    return df

def etl_transform(df, profile):
    """Transform: Create derived columns, normalize, aggregate, add business logic"""
    numeric_stats = profile.get('dataProfile', {}).get('numericStats', {})
    
    # Normalization: Z-score and Min-Max scaling
    for col_name, stats in numeric_stats.items():
        if col_name in df.columns:
            mean_val = stats.get('mean')
            std_val = stats.get('stddev')
            min_val = stats.get('min')
            max_val = stats.get('max')
            
            # Convert to float if needed
            if mean_val is not None:
                mean_val = float(mean_val)
            if std_val is not None:
                std_val = float(std_val)
            if min_val is not None:
                min_val = float(min_val)
            if max_val is not None:
                max_val = float(max_val)
            
            # Z-score normalization
            if mean_val is not None and std_val and std_val > 0:
                df = df.withColumn(f"{col_name}_zscore", 
                    spark_round((col(col_name) - lit(mean_val)) / lit(std_val), 4))
            
            # Min-Max scaling (0-1)
            if min_val is not None and max_val is not None and max_val > min_val:
                df = df.withColumn(f"{col_name}_minmax", 
                    spark_round((col(col_name) - lit(min_val)) / lit(max_val - min_val), 4))
            
            # Binning into categories
            if mean_val is not None:
                df = df.withColumn(f"{col_name}_category",
                    when(col(col_name) < mean_val * 0.5, 'LOW')
                    .when(col(col_name) < mean_val * 1.5, 'MEDIUM')
                    .otherwise('HIGH')
                )
    
    # Add row number for tracking
    df = df.withColumn('row_id', row_number().over(Window.orderBy(lit(1))))
    
    return df

def run_etl(profile_path, input_data_path, s3_output_path, local_output_dir):
    print(f"Reading profiling report from {profile_path}...")
    profile = read_json_from_s3(profile_path)
    
    recommendations = profile.get('recommendations', [])
    clean_needed = any(r['process'] == 'ETL_CLEAN' and r['required'] for r in recommendations)
    transform_needed = any(r['process'] == 'ETL_TRANSFORM' and r['required'] for r in recommendations)
    
    print(f"ETL Clean needed: {clean_needed}")
    print(f"ETL Transform needed: {transform_needed}")
    
    print(f"Reading input data from {input_data_path}...")
    data = read_json_from_s3(input_data_path)
    df = spark.createDataFrame(data)
    
    original_count = df.count()
    
    if clean_needed:
        print("Performing ETL Clean...")
        df = etl_clean(df, profile)
    
    if transform_needed:
        print("Performing ETL Transform...")
        df = etl_transform(df, profile)
    
    final_data = [row.asDict() for row in df.collect()]
    final_count = len(final_data)
    
    # Save to S3
    etl_s3 = s3_output_path.rstrip('/') + '/etl_processed_data.json'
    print(f"Writing to {etl_s3}...")
    write_json_to_s3(etl_s3, final_data)
    
    # Save locally
    local_path = Path(local_output_dir) / "etl_processed_data.json"
    print(f"Writing to {local_path}...")
    write_json_to_local(local_path, final_data)
    
    print(f"\n✓ ETL complete!")
    print(f"  Records processed: {original_count}")
    print(f"  Final records: {final_count}")
    print(f"  S3: {etl_s3}")
    print(f"  Local: {local_path}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python etl_processing.py <profile_report_s3> <input_data_s3> <s3_output_path> <local_output_dir>")
        print("Example: python etl_processing.py s3://bucket/report.json s3://bucket/data.json s3://bucket/output/ /path/to/local/")
        sys.exit(1)
    
    profile_path = sys.argv[1]
    input_data_path = sys.argv[2]
    s3_output = sys.argv[3]
    local_output = sys.argv[4]
    
    run_etl(profile_path, input_data_path, s3_output, local_output)
