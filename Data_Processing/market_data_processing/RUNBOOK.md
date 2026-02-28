# Market Data Processing Pipeline - Runbook

## Configuration

```bash
S3_INPUT="s3://tanmayrawtest101/fin_work/datasets/market_data/"
S3_OUTPUT="s3://tanmayrawtest101/fin_work/process_data/market_data/"
LOCAL_OUTPUT="/home/tanmay-axcess/Desktop/my/Data_Processing/market_data_processing/outputs"
SCRIPT_DIR="/home/tanmay-axcess/Desktop/my/Data_Processing/market_data_processing/Src"
```

## Stage 1: Data Profiling

**Purpose:** Analyze CSV structure, detect schema, PII, and statistics

**Arguments:**
- `arg1`: S3 input CSV path
- `arg2`: S3 output report path

```bash
cd $SCRIPT_DIR

python3 data_profiling.py \
  ${S3_INPUT}stock_data.csv \
  ${S3_OUTPUT}profiling_output/report.json
```

**Output:**
- S3: `s3://tanmayrawtest101/fin_work/process_data/market_data/profiling_output/report.json`
- Local: `outputs/report.json`

---

## Stage 2: Deduplication

**Purpose:** Remove duplicate records based on key columns

**Arguments:**
- `arg1`: S3 profiling report path
- `arg2`: S3 raw data path
- `arg3`: S3 output directory
- `arg4`: Local output directory

```bash
cd $SCRIPT_DIR

python3 deduplication.py \
  ${S3_OUTPUT}profiling_output/report.json \
  ${S3_INPUT}stock_data.csv \
  ${S3_OUTPUT}dedup_output \
  $LOCAL_OUTPUT
```

**Output:**
- S3: `s3://tanmayrawtest101/fin_work/process_data/market_data/dedup_output/deduplicated_data.json`
- Local: `outputs/deduplicated_data.json`

---

## Stage 3: PII Masking

**Purpose:** Mask sensitive columns with half-masking

**Arguments:**
- `arg1`: S3 profiling report path
- `arg2`: S3 deduplicated data path
- `arg3`: S3 output directory
- `arg4`: Local output directory

```bash
cd $SCRIPT_DIR

python3 pii_masking.py \
  ${S3_OUTPUT}profiling_output/report.json \
  ${S3_OUTPUT}dedup_output/deduplicated_data.json \
  ${S3_OUTPUT}pii_masked_output \
  $LOCAL_OUTPUT
```

**Output:**
- S3: `s3://tanmayrawtest101/fin_work/process_data/market_data/pii_masked_output/pii_masked_data.json`
- Local: `outputs/pii_masked_data.json`

---

## Stage 4: ETL Processing

**Purpose:** Clean data and create derived columns

**Arguments:**
- `arg1`: S3 profiling report path
- `arg2`: S3 PII masked data path
- `arg3`: S3 output directory
- `arg4`: Local output directory

```bash
cd $SCRIPT_DIR

python3 etl_processing.py \
  ${S3_OUTPUT}profiling_output/report.json \
  ${S3_OUTPUT}pii_masked_output/pii_masked_data.json \
  ${S3_OUTPUT}etl_output \
  $LOCAL_OUTPUT
```

**Output:**
- S3: `s3://tanmayrawtest101/fin_work/process_data/market_data/etl_output/etl_processed_data.json`
- Local: `outputs/etl_processed_data.json`

---

## Stage 5: Quality Check

**Purpose:** Validate data quality with 7 checks

**Arguments:**
- `arg1`: S3 ETL processed data path
- `arg2`: S3 output directory
- `arg3`: Local output directory

```bash
cd $SCRIPT_DIR

python3 quality_check.py \
  ${S3_OUTPUT}etl_output/etl_processed_data.json \
  ${S3_OUTPUT}quality_check_output \
  $LOCAL_OUTPUT
```

**Output:**
- S3: `s3://tanmayrawtest101/fin_work/process_data/market_data/quality_check_output/quality_check_report.json`
- Local: `outputs/quality_check_report.json`

---

## Stage 6: Final Processing

**Purpose:** Fix quality issues and save as Parquet

**Arguments:**
- `arg1`: S3 quality report path
- `arg2`: S3 ETL processed data path
- `arg3`: S3 output directory
- `arg4`: Local output directory

```bash
cd $SCRIPT_DIR

python3 final_processing.py \
  ${S3_OUTPUT}quality_check_output/quality_check_report.json \
  ${S3_OUTPUT}etl_output/etl_processed_data.json \
  ${S3_OUTPUT}final_output \
  $LOCAL_OUTPUT
```

**Output:**
- S3: `s3://tanmayrawtest101/fin_work/process_data/market_data/final_output/final_processed_data.parquet`
- S3: `s3://tanmayrawtest101/fin_work/process_data/market_data/final_output/final_processed_data.json`
- S3: `s3://tanmayrawtest101/fin_work/process_data/market_data/final_output/final_processing_report.json`
- Local: `outputs/final_processed_data.parquet`
- Local: `outputs/final_processed_data.json`
- Local: `outputs/final_processing_report.json`

---

## Run All Stages

```bash
#!/bin/bash

# Configuration
S3_INPUT="s3://tanmayrawtest101/fin_work/datasets/market_data/"
S3_OUTPUT="s3://tanmayrawtest101/fin_work/process_data/market_data/"
LOCAL_OUTPUT="/home/tanmay-axcess/Desktop/my/Data_Processing/market_data_processing/outputs"
SCRIPT_DIR="/home/tanmay-axcess/Desktop/my/Data_Processing/market_data_processing/Src"

cd $SCRIPT_DIR

# Stage 1: Data Profiling
echo "Stage 1: Data Profiling..."
python3 data_profiling.py \
  ${S3_INPUT}stock_data.csv \
  ${S3_OUTPUT}profiling_output/report.json

# Stage 2: Deduplication
echo "Stage 2: Deduplication..."
python3 deduplication.py \
  ${S3_OUTPUT}profiling_output/report.json \
  ${S3_INPUT}stock_data.csv \
  ${S3_OUTPUT}dedup_output \
  $LOCAL_OUTPUT

# Stage 3: PII Masking
echo "Stage 3: PII Masking..."
python3 pii_masking.py \
  ${S3_OUTPUT}profiling_output/report.json \
  ${S3_OUTPUT}dedup_output/deduplicated_data.json \
  ${S3_OUTPUT}pii_masked_output \
  $LOCAL_OUTPUT

# Stage 4: ETL Processing
echo "Stage 4: ETL Processing..."
python3 etl_processing.py \
  ${S3_OUTPUT}profiling_output/report.json \
  ${S3_OUTPUT}pii_masked_output/pii_masked_data.json \
  ${S3_OUTPUT}etl_output \
  $LOCAL_OUTPUT

# Stage 5: Quality Check
echo "Stage 5: Quality Check..."
python3 quality_check.py \
  ${S3_OUTPUT}etl_output/etl_processed_data.json \
  ${S3_OUTPUT}quality_check_output \
  $LOCAL_OUTPUT

# Stage 6: Final Processing
echo "Stage 6: Final Processing..."
python3 final_processing.py \
  ${S3_OUTPUT}quality_check_output/quality_check_report.json \
  ${S3_OUTPUT}etl_output/etl_processed_data.json \
  ${S3_OUTPUT}final_output \
  $LOCAL_OUTPUT

echo "Pipeline completed!"
```

## Script Arguments Summary

| Script | Arg 1 | Arg 2 | Arg 3 | Arg 4 |
|--------|-------|-------|-------|-------|
| data_profiling.py | S3 input CSV | S3 output report | - | - |
| deduplication.py | S3 profile report | S3 raw data | S3 output dir | Local output dir |
| pii_masking.py | S3 profile report | S3 dedup data | S3 output dir | Local output dir |
| etl_processing.py | S3 profile report | S3 masked data | S3 output dir | Local output dir |
| quality_check.py | S3 ETL data | S3 output dir | Local output dir | - |
| final_processing.py | S3 quality report | S3 ETL data | S3 output dir | Local output dir |
