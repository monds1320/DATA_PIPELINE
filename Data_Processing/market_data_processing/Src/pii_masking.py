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

def mask_pii(data, pii_columns):
    if not pii_columns:
        return data
    
    masked_data = []
    for row in data:
        masked_row = row.copy()
        for pii_col in pii_columns:
            if pii_col in masked_row and masked_row[pii_col] is not None:
                value = str(masked_row[pii_col])
                half = len(value) // 2
                masked_row[pii_col] = value[:half] + '*' * len(value[half:])
        masked_data.append(masked_row)
    
    return masked_data

def run_pii_masking(profile_path, dedup_data_path, s3_output_path, local_output_dir):
    print(f"Reading profiling report from {profile_path}...")
    profile = read_json_from_s3(profile_path)
    
    pii_columns = profile.get('dataProfile', {}).get('piiColumns', [])
    print(f"PII columns detected: {pii_columns if pii_columns else 'None'}")
    
    print(f"Reading deduplicated data from {dedup_data_path}...")
    data = read_json_from_s3(dedup_data_path)
    
    original_count = len(data)
    
    if not pii_columns:
        print("✓ No PII columns found. Saving data as-is.")
        masked_data = data
    else:
        print(f"Masking {len(pii_columns)} PII columns in {original_count} records...")
        masked_data = mask_pii(data, pii_columns)
    
    masked_s3 = s3_output_path.rstrip('/') + '/pii_masked_data.json'
    print(f"Writing to {masked_s3}...")
    write_json_to_s3(masked_s3, masked_data)
    
    local_path = Path(local_output_dir) / "pii_masked_data.json"
    print(f"Writing to {local_path}...")
    write_json_to_local(local_path, masked_data)
    
    print(f"\n✓ PII Masking complete!")
    print(f"  Records processed: {original_count}")
    print(f"  PII columns masked: {len(pii_columns)}")
    print(f"  S3: {masked_s3}")
    print(f"  Local: {local_path}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python pii_masking.py <profile_report_s3> <dedup_data_s3> <s3_output_path> <local_output_dir>")
        sys.exit(1)
    
    profile_path = sys.argv[1]
    dedup_data_path = sys.argv[2]
    s3_output = sys.argv[3]
    local_output = sys.argv[4]
    
    run_pii_masking(profile_path, dedup_data_path, s3_output, local_output)
