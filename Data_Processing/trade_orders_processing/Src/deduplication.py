import json
import boto3
import sys
from pathlib import Path

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

def deduplicate_data(data, columns):
    """Deduplicate using window function approach"""
    if not data or not columns:
        return data
    
    # Create unique key for each row
    seen = set()
    deduped = []
    
    for row in data:
        # Create row signature
        row_key = tuple(row.get(col) for col in columns)
        if row_key not in seen:
            seen.add(row_key)
            deduped.append(row)
    
    return deduped

def run_deduplication(profile_path, raw_data_path, s3_output_path, local_output_dir):
    print(f"Reading profiling report from {profile_path}...")
    profile = read_json_from_s3(profile_path)
    
    duplicate_count = profile.get('dataProfile', {}).get('duplicateCount', 0)
    
    print(f"Duplicate count: {duplicate_count}")
    
    print(f"Reading raw data from {raw_data_path}...")
    raw_data = read_json_from_s3(raw_data_path)
    
    original_count = len(raw_data)
    
    if duplicate_count == 0:
        print("✓ No duplicates found. Saving data as-is.")
        deduped_data = raw_data
    else:
        columns = list(raw_data[0].keys()) if raw_data else []
        print(f"Deduplicating {original_count} records...")
        deduped_data = deduplicate_data(raw_data, columns)
    
    final_count = len(deduped_data)
    removed = original_count - final_count
    
    # Save to S3
    dedup_s3 = s3_output_path.rstrip('/') + '/deduplicated_data.json'
    print(f"Writing to {dedup_s3}...")
    write_json_to_s3(dedup_s3, deduped_data)
    
    # Save locally
    local_path = Path(local_output_dir) / "deduplicated_data.json"
    print(f"Writing to {local_path}...")
    write_json_to_local(local_path, deduped_data)
    
    print(f"\n✓ Deduplication complete!")
    print(f"  Original: {original_count} rows")
    print(f"  Removed: {removed} duplicates")
    print(f"  Final: {final_count} rows")
    print(f"  S3: {dedup_s3}")
    print(f"  Local: {local_path}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python deduplication.py <profile_report_s3> <raw_data_s3> <s3_output_path> <local_output_dir>")
        print("Example: python deduplication.py s3://bucket/report.json s3://bucket/data.json s3://bucket/output/ /path/to/local/")
        sys.exit(1)
    
    profile_path = sys.argv[1]
    raw_data_path = sys.argv[2]
    s3_output = sys.argv[3]
    local_output = sys.argv[4]
    
    run_deduplication(profile_path, raw_data_path, s3_output, local_output)
