# Transaction Data - Bank Account Transactions

## Overview
Real bank account transaction data from Kaggle containing actual banking operations including deposits, withdrawals, and balance tracking. Raw transactional data suitable for fraud detection, pattern analysis, and financial modeling.

## Dataset Details

- **Total Records**: 116,201
- **Source**: Kaggle - Bank Transaction Dataset
- **Format**: Excel (XLSX), JSON (streaming), Parquet
- **Time Period**: 2017-2018
- **Data Type**: Raw transaction logs

## Data Schema

| Column | Type | Description |
|--------|------|-------------|
| Account No | string | Bank account number |
| DATE | date | Transaction date (YYYY-MM-DD) |
| TRANSACTION DETAILS | string | Description of transaction |
| CHQ.NO. | string | Cheque number (if applicable) |
| VALUE DATE | date | Value date for transaction |
| WITHDRAWAL AMT | float | Withdrawal amount (debit) |
| DEPOSIT AMT | float | Deposit amount (credit) |
| BALANCE AMT | float | Account balance after transaction |

## Transaction Types

Based on TRANSACTION DETAILS field:
- **Deposits**: Cash deposits, cheque deposits, transfers in
- **Withdrawals**: Cash withdrawals, ATM transactions, transfers out
- **Payments**: Bill payments, card swipes, UPI payments
- **Transfers**: NEFT, IMPS, RTGS
- **Charges**: Bank fees, service charges

## File Formats

### Excel (Original)
- **File**: bank.xlsx
- **Format**: Microsoft Excel
- **Use**: Manual analysis, reporting

### JSON (Streaming/Line-Delimited)
```json
{"Account No":"409000611074","DATE":"2017-06-29","TRANSACTION DETAILS":"DEPOSIT","WITHDRAWAL AMT":null,"DEPOSIT AMT":1000000.0,"BALANCE AMT":1000000.0}
```
- **Protocol**: ISO 20022, REST APIs
- **Use**: Kafka streaming, real-time processing

### Parquet (Columnar Storage)
- **Compression**: Snappy
- **Use**: Data lakes (S3), analytics (Athena, EMR)
- **Optimized for**: Batch processing, ML pipelines

## Use Cases

### Real-time Fraud Detection
- Monitor unusual withdrawal patterns
- Detect rapid balance changes
- Flag suspicious transaction sequences

### Risk Scoring
- Calculate transaction velocity
- Analyze spending patterns
- Assess account behavior

### AML/KYC Compliance
- Track large transactions (>₹10 lakh)
- Monitor cross-border transfers
- Identify suspicious activities

### Financial Analytics
- Cash flow analysis
- Balance forecasting
- Customer segmentation

## Industry Standards

- **PCI-DSS** - Payment Card Industry Data Security Standard
- **ISO 20022** - Financial messaging standard
- **AML** - Anti-Money Laundering regulations
- **KYC** - Know Your Customer compliance

## AWS Services Integration

| Service | Purpose |
|---------|---------|
| **MSK (Kafka)** | Stream transaction events in real-time |
| **S3** | Store raw transaction data in data lake |
| **Glue** | ETL processing and data cataloging |
| **EMR** | Big data analytics on transaction history |
| **Kinesis** | Real-time data ingestion |
| **Athena** | SQL queries on Parquet files |
| **SageMaker** | ML models for fraud detection |

## Data Processing

### Convert to JSON (Streaming)
```python
import pandas as pd

df = pd.read_excel('bank.xlsx')
df.to_json('transactions.json', orient='records', lines=True)
```

### Convert to Parquet
```python
import pandas as pd

df = pd.read_excel('bank.xlsx')
df.to_parquet('transactions.parquet', index=False)
```

### Load and Analyze
```python
import pandas as pd

# Load data
df = pd.read_parquet('transactions.parquet')

# Calculate total deposits
total_deposits = df['DEPOSIT AMT'].sum()

# Find large withdrawals
large_withdrawals = df[df['WITHDRAWAL AMT'] > 100000]

# Group by account
account_summary = df.groupby('Account No').agg({
    'DEPOSIT AMT': 'sum',
    'WITHDRAWAL AMT': 'sum',
    'BALANCE AMT': 'last'
})
```

## Data Characteristics

- **High-volume**: 116K+ transactions
- **Low-latency**: Suitable for real-time processing
- **Partitioned**: Can be partitioned by date/account
- **Raw format**: Unprocessed transaction logs
- **Real-world**: Actual banking operations

## Sample Transactions

```
Account No: 409000611074
Date: 2017-06-29
Type: DEPOSIT
Amount: ₹10,00,000
Balance: ₹10,00,000

Account No: 409000611074
Date: 2017-07-05
Type: DEPOSIT
Amount: ₹10,00,000
Balance: ₹20,00,000
```

## AI/ML Applications

- **Fraud Detection**: Identify anomalous transaction patterns
- **Risk Scoring**: Calculate customer risk profiles
- **Balance Forecasting**: Predict future account balances
- **Customer Segmentation**: Group customers by behavior
- **Churn Prediction**: Identify accounts at risk of closure

## Notes

- All amounts in Indian Rupees (₹)
- Contains real transaction patterns
- Suitable for production-like testing
- Can be used for ML model training
- Anonymized account numbers

## License

Dataset from Kaggle. For educational and research purposes.
