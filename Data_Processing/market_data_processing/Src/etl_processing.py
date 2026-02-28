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

def etl_clean(data, profile):
    """Clean: Handle missing values, fix data types - dynamically detect columns"""
    cleaned = []
    null_counts = profile.get('dataProfile', {}).get('nullCounts', {})
    
    # Get all columns from first row
    sample_row = data[0] if data else {}
    all_cols = list(sample_row.keys())
    
    # Dynamically detect numeric columns
    numeric_cols = []
    string_cols = []
    
    for col in all_cols:
        # Check if column looks numeric
        try:
            sample_vals = [row.get(col) for row in data[:10] if row.get(col)]
            if sample_vals:
                float(sample_vals[0])
                numeric_cols.append(col)
        except:
            string_cols.append(col)
    
    for row in data:
        cleaned_row = {}
        for col, value in row.items():
            if value == '' or value is None:
                if col in numeric_cols:
                    cleaned_row[col] = 0.0
                else:
                    cleaned_row[col] = value
            else:
                if col in numeric_cols:
                    try:
                        # Check if it's a volume/count column (integer)
                        if any(kw in col.lower() for kw in ['volume', 'count', 'quantity']):
                            cleaned_row[col] = int(float(value))
                        else:
                            cleaned_row[col] = float(value)
                    except:
                        cleaned_row[col] = 0.0
                else:
                    cleaned_row[col] = value
        cleaned.append(cleaned_row)
    
    return cleaned

def etl_transform(data, profile):
    """Transform: Create derived columns - dynamically detect price/volume columns"""
    transformed = []
    
    # Dynamically find key columns
    sample_row = data[0] if data else {}
    symbol_col = next((col for col in sample_row.keys() if any(kw in col.lower() for kw in ['symbol', 'ticker', 'stock'])), None)
    date_col = next((col for col in sample_row.keys() if 'date' in col.lower()), None)
    high_col = next((col for col in sample_row.keys() if 'high' in col.lower()), None)
    low_col = next((col for col in sample_row.keys() if 'low' in col.lower()), None)
    open_col = next((col for col in sample_row.keys() if 'open' in col.lower()), None)
    close_col = next((col for col in sample_row.keys() if 'close' in col.lower()), None)
    volume_cols = [col for col in sample_row.keys() if 'volume' in col.lower()]
    
    for i, row in enumerate(data):
        new_row = row.copy()
        
        # Calculate daily return (if close column exists)
        if close_col and symbol_col and i > 0 and data[i-1].get(symbol_col) == row.get(symbol_col):
            try:
                prev_close = float(data[i-1].get(close_col, 0))
                curr_close = float(row.get(close_col, 0))
                if prev_close > 0:
                    new_row['daily_return'] = round((curr_close - prev_close) / prev_close * 100, 4)
                else:
                    new_row['daily_return'] = 0.0
            except:
                new_row['daily_return'] = 0.0
        else:
            new_row['daily_return'] = 0.0
        
        # Calculate intraday range (if high and low exist)
        if high_col and low_col:
            try:
                high = float(row.get(high_col, 0))
                low = float(row.get(low_col, 0))
                new_row['intraday_range'] = round(high - low, 2)
            except:
                new_row['intraday_range'] = 0.0
        
        # Calculate price change (if open and close exist)
        if open_col and close_col:
            try:
                open_price = float(row.get(open_col, 0))
                close_price = float(row.get(close_col, 0))
                new_row['price_change'] = round(close_price - open_price, 2)
                
                # Calculate price change percentage
                if open_price > 0:
                    new_row['price_change_pct'] = round((close_price - open_price) / open_price * 100, 4)
                else:
                    new_row['price_change_pct'] = 0.0
            except:
                new_row['price_change'] = 0.0
                new_row['price_change_pct'] = 0.0
        
        # Categorize volume (if volume column exists)
        if volume_cols:
            try:
                volume = int(row.get(volume_cols[0], 0))
                if volume < 1000000:
                    new_row['volume_category'] = 'LOW'
                elif volume < 10000000:
                    new_row['volume_category'] = 'MEDIUM'
                else:
                    new_row['volume_category'] = 'HIGH'
            except:
                new_row['volume_category'] = 'UNKNOWN'
        
        # Extract date components (if date column exists)
        if date_col:
            date_str = row.get(date_col, '')
            if date_str:
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    new_row['year'] = date_obj.year
                    new_row['month'] = date_obj.month
                    new_row['day'] = date_obj.day
                    new_row['day_of_week'] = date_obj.strftime('%A')
                except:
                    pass
        
        transformed.append(new_row)
    
    return transformed

def run_etl(profile_path, input_data_path, s3_output_path, local_output_dir):
    print(f"Reading profiling report from {profile_path}...")
    profile = read_json_from_s3(profile_path)
    
    print(f"Reading input data from {input_data_path}...")
    data = read_json_from_s3(input_data_path)
    
    original_count = len(data)
    
    print("Performing ETL Clean...")
    cleaned_data = etl_clean(data, profile)
    
    print("Performing ETL Transform...")
    transformed_data = etl_transform(cleaned_data, profile)
    
    final_count = len(transformed_data)
    
    etl_s3 = s3_output_path.rstrip('/') + '/etl_processed_data.json'
    print(f"Writing to {etl_s3}...")
    write_json_to_s3(etl_s3, transformed_data)
    
    local_path = Path(local_output_dir) / "etl_processed_data.json"
    print(f"Writing to {local_path}...")
    write_json_to_local(local_path, transformed_data)
    
    print(f"\n✓ ETL complete!")
    print(f"  Records processed: {original_count}")
    print(f"  Final records: {final_count}")
    print(f"  S3: {etl_s3}")
    print(f"  Local: {local_path}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python etl_processing.py <profile_report_s3> <input_data_s3> <s3_output_path> <local_output_dir>")
        sys.exit(1)
    
    profile_path = sys.argv[1]
    input_data_path = sys.argv[2]
    s3_output = sys.argv[3]
    local_output = sys.argv[4]
    
    run_etl(profile_path, input_data_path, s3_output, local_output)
