# Market Data Processing Pipeline

## Overview
Complete 6-stage data processing pipeline for stock market data with **dynamic column detection**. Works with ANY stock dataset naming convention - no code changes needed!

## Key Features

✅ **Dynamic Column Detection** - Works with any CSV format (Yahoo Finance, Alpha Vantage, custom)  
✅ **6-Stage Pipeline** - Profile → Deduplicate → Mask PII → ETL → Quality Check → Final Processing  
✅ **CSV to Parquet** - Optimized columnar storage  
✅ **S3 Integration** - Read from and write to S3  
✅ **Quality Validation** - 7 automated checks with auto-fixing  
✅ **Stock Transformations** - Returns, ranges, categories, date components

## Dataset
- **Source**: s3://tanmayrawtest101/fin_work/datasets/market_data/stock_data.csv
- **Format**: CSV
- **Records**: ~24,655 stock records
- **Stocks**: RELIANCE.NS, TCS.NS, INFY.NS, HDFCBANK.NS, WIPRO.NS
- **Period**: 2006-2026 (~20 years)

## Dynamic Column Detection

The pipeline automatically detects columns by keywords - **no hardcoded column names**!

| Your Column Names | Pipeline Detects |
|-------------------|------------------|
| `Open`, `opening_price`, `OPEN` | ✓ Open price |
| `High`, `HIGH`, `high_price` | ✓ High price |
| `Low`, `LOW`, `lowest` | ✓ Low price |
| `Close`, `closing_price` | ✓ Close price |
| `Volume`, `trading_volume` | ✓ Volume |
| `symbol`, `ticker`, `stock` | ✓ Symbol |
| `date`, `trading_date`, `timestamp` | ✓ Date |

**Works with:** Yahoo Finance, Alpha Vantage, custom formats, crypto prices, commodity prices

## Pipeline Stages

### Stage 1: Data Profiling
- Analyzes CSV structure dynamically
- Detects all columns and data types
- Identifies null values and duplicates
- Detects PII columns
- Generates statistics

### Stage 2: Deduplication
- Dynamically finds key columns (symbol, date)
- Removes duplicate records
- Preserves unique records

### Stage 3: PII Masking
- Detects PII columns automatically
- Half-masking: first half visible, second half masked

### Stage 4: ETL Processing
**Clean:**
- Handle missing values
- Fix data types (auto-detect numeric columns)
- Remove outliers

**Transform (creates derived columns):**
- `daily_return` - Daily % return
- `intraday_range` - High - Low
- `price_change` - Close - Open
- `price_change_pct` - % change
- `volume_category` - LOW/MEDIUM/HIGH
- `year`, `month`, `day`, `day_of_week` - Date components

### Stage 5: Quality Check
7 automated quality checks:
1. **Completeness** - Missing values
2. **Data Types** - Numeric/string validation
3. **Business Rules** - Price relationships (high >= low, close in range)
4. **Duplicates** - Duplicate detection
5. **Consistency** - Valid symbols, date format
6. **Statistical Outliers** - Z-score > 3
7. **Data Distribution** - Skewed data detection

### Stage 6: Final Processing
- Fix all quality issues automatically
- Cap statistical outliers at ±3σ
- Fix business rule violations
- Remove duplicates
- Save as **Parquet** (optimized) + **JSON** (compatible)
- Generate processing report

## Directory Structure
```
market_data_processing/
├── Src/
│   ├── data_profiling.py      # Stage 1: Profile CSV
│   ├── deduplication.py        # Stage 2: Remove duplicates
│   ├── pii_masking.py          # Stage 3: Mask PII
│   ├── etl_processing.py       # Stage 4: Clean & transform
│   ├── quality_check.py        # Stage 5: Validate quality
│   └── final_processing.py     # Stage 6: Fix & save Parquet
├── outputs/
│   ├── report.json
│   ├── deduplicated_data.json
│   ├── pii_masked_data.json
│   ├── etl_processed_data.json
│   ├── quality_check_report.json
│   ├── final_processed_data.parquet
│   ├── final_processed_data.json
│   └── final_processing_report.json
└── README.md                   # This file
```

## S3 Output Structure
```
s3://tanmayrawtest101/fin_work/process_data/market_data/
├── profiling_output/report.json
├── dedup_output/deduplicated_data.json
├── pii_masked_output/pii_masked_data.json
├── etl_output/etl_processed_data.json
├── quality_check_output/quality_check_report.json
└── final_output/
    ├── final_processed_data.parquet  # Final optimized output
    ├── final_processed_data.json
    └── final_processing_report.json
```

## Quick Start

### 1. Install Dependencies
```bash
pip install boto3 pandas pyarrow
```

### 2. Run Pipeline
```bash
cd /home/tanmay-axcess/Desktop/my/Data_Processing/market_data_processing/Src

# Stage 1: Profile
python3 data_profiling.py \
  s3://tanmayrawtest101/fin_work/datasets/market_data/stock_data.csv \
  s3://tanmayrawtest101/fin_work/process_data/market_data/profiling_output/report.json

# Stage 2: Deduplicate
python3 deduplication.py \
  s3://tanmayrawtest101/fin_work/process_data/market_data/profiling_output/report.json \
  s3://tanmayrawtest101/fin_work/datasets/market_data/stock_data.csv \
  s3://tanmayrawtest101/fin_work/process_data/market_data/dedup_output \
  ../outputs

# Stage 3: Mask PII
python3 pii_masking.py \
  s3://tanmayrawtest101/fin_work/process_data/market_data/profiling_output/report.json \
  s3://tanmayrawtest101/fin_work/process_data/market_data/dedup_output/deduplicated_data.json \
  s3://tanmayrawtest101/fin_work/process_data/market_data/pii_masked_output \
  ../outputs

# Stage 4: ETL
python3 etl_processing.py \
  s3://tanmayrawtest101/fin_work/process_data/market_data/profiling_output/report.json \
  s3://tanmayrawtest101/fin_work/process_data/market_data/pii_masked_output/pii_masked_data.json \
  s3://tanmayrawtest101/fin_work/process_data/market_data/etl_output \
  ../outputs

# Stage 5: Quality Check
python3 quality_check.py \
  s3://tanmayrawtest101/fin_work/process_data/market_data/etl_output/etl_processed_data.json \
  s3://tanmayrawtest101/fin_work/process_data/market_data/quality_check_output \
  ../outputs

# Stage 6: Final Processing
python3 final_processing.py \
  s3://tanmayrawtest101/fin_work/process_data/market_data/quality_check_output/quality_check_report.json \
  s3://tanmayrawtest101/fin_work/process_data/market_data/etl_output/etl_processed_data.json \
  s3://tanmayrawtest101/fin_work/process_data/market_data/final_output \
  ../outputs
```

### 3. Use Your Own Dataset
```bash
# Upload your CSV (any column naming works!)
aws s3 cp your_data.csv s3://tanmayrawtest101/fin_work/datasets/market_data/

# Run pipeline - it auto-adapts to your column names!
python3 data_profiling.py s3://.../your_data.csv s3://.../report.json
# ... continue with other stages
```

## Testing with Different Datasets

The pipeline works with **any** stock market CSV format:

| Dataset Format | Columns | Result |
|----------------|---------|--------|
| Yahoo Finance | Date, Open, High, Low, Close, Volume | ✓ Works |
| Alpha Vantage | timestamp, 1.open, 2.high, 3.low, 4.close | ✓ Works |
| Custom | ticker, trading_date, opening_price, closing_price | ✓ Works |
| Minimal | symbol, date, close | ✓ Works (skips missing transformations) |

## Comparison with Trade Orders Pipeline

| Feature | Trade Orders | Market Data |
|---------|-------------|-------------|
| Scripts | 6 | 6 |
| Stages | 6 | 6 |
| Input | JSON | CSV |
| Processing | PySpark | Pandas |
| Column Detection | Schema-based | **Dynamic** ✓ |
| Output | Parquet + JSON | Parquet + JSON |
| Reusability | Single format | **Any format** ✓ |

## Dependencies
```bash
pip install boto3 pandas pyarrow
```

- **boto3** - AWS S3 integration
- **pandas** - Data manipulation
- **pyarrow** - Parquet format support
- **Python 3.x** - Runtime
- **AWS credentials** - Configured

## Output Files

**S3 Location:** `s3://tanmayrawtest101/fin_work/process_data/market_data/`  
**Local Location:** `outputs/`

- `report.json` - Profiling report
- `deduplicated_data.json` - Deduplicated data
- `pii_masked_data.json` - PII masked data
- `etl_processed_data.json` - Transformed data
- `quality_check_report.json` - Quality report
- `final_processed_data.parquet` - **Final output (optimized)**
- `final_processed_data.json` - Final output (JSON)
- `final_processing_report.json` - Processing report

## Notes

- ✅ **No hardcoded column names** - works with any CSV format
- ✅ **Graceful degradation** - skips transformations if columns missing
- ✅ **Production ready** - fully tested and documented
- ✅ **Reusable** - works with stocks, crypto, commodities
- ✅ **Auto-fixing** - quality issues fixed automatically in Stage 6
