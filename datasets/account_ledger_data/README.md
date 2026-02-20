# Account & Ledger Data

## Overview
Synthetic account and ledger data representing a banking system with double-entry bookkeeping. Contains account master data and detailed transaction ledger entries with ACID compliance structure.

## Dataset Details

- **Total Accounts**: 5,000
- **Active Accounts**: 2,981
- **Total Ledger Entries**: 30,183
- **Format**: Parquet (columnar storage)
- **Data Type**: Account master data + Transaction ledger

## Data Structure

### Two Dependent Datasets:

1. **Account Data** (Master) - Static account information
2. **Ledger Data** (Transactional) - All financial transactions

**Relationship**: One account → Many ledger entries

## Account Data Schema

| Column | Type | Description |
|--------|------|-------------|
| account_id | string | Unique account identifier (ACC00000001) |
| account_number | string | Bank account number (10 digits) |
| customer_id | string | Customer identifier (CUST000001) |
| account_type | string | SAVINGS, CURRENT, FIXED_DEPOSIT, RECURRING_DEPOSIT |
| account_status | string | ACTIVE, DORMANT, CLOSED |
| opening_date | date | Account opening date |
| branch_code | string | Branch identifier (BR1000) |
| currency | string | Currency code (INR) |
| current_balance | float | Current account balance (₹) |
| available_balance | float | Available balance for withdrawal (₹) |
| overdraft_limit | float | Overdraft facility limit (₹) |
| interest_rate | float | Interest rate (%) |
| last_transaction_date | date | Last transaction date |

## Ledger Data Schema

| Column | Type | Description |
|--------|------|-------------|
| entry_id | string | Unique ledger entry ID (LED0000000001) |
| account_id | string | Links to Account Data |
| transaction_date | date | Transaction date |
| value_date | date | Value date for interest calculation |
| transaction_type | string | DEPOSIT, WITHDRAWAL, TRANSFER_IN, TRANSFER_OUT, INTEREST, FEE, CHARGE |
| debit_amount | float | Debit amount (money out) |
| credit_amount | float | Credit amount (money in) |
| balance | float | Running balance after transaction |
| description | string | Transaction description |
| reference_number | string | Transaction reference (REF123456789) |
| branch_code | string | Branch where transaction occurred |
| posted_by | string | User who posted the entry (USER1234) |
| posted_timestamp | timestamp | When entry was posted |

## File Format

### Parquet (Columnar Storage)
- **Files**: accounts.parquet, ledger.parquet
- **Compression**: Snappy
- **Use**: Data lakes, batch analytics
- **Optimized for**: S3, Glue, Athena, EMR

## Statistics

### Accounts
- Total Balance: ₹2.52 Billion
- Average Balance: ₹5.04 Lakh
- Active Rate: 59.6%

### Ledger
- Total Debits: ₹378.58 Million
- Total Credits: ₹376.49 Million
- Avg Entries per Account: ~30

## Use Cases

### Credit Risk Modeling
- Analyze account balance trends
- Calculate credit utilization
- Assess overdraft usage patterns

### Loan Approval
- Verify account history
- Check transaction patterns
- Validate income deposits

### ACID Compliance
- Double-entry bookkeeping
- Transaction atomicity
- Balance reconciliation

### Financial Analytics
- Cash flow analysis
- Account aging analysis
- Dormancy prediction

## Industry Standards

- **SWIFT** - Society for Worldwide Interbank Financial Telecommunication
- **ISO 8583** - Financial transaction card messaging
- **Basel III** - Banking supervision regulations
- **SOX** - Sarbanes-Oxley Act compliance

## AWS Services Integration

| Service | Purpose |
|---------|---------|
| **Aurora** | Transactional database for ledger |
| **S3** | Data lake storage for Parquet files |
| **Glue** | ETL and data cataloging |
| **Athena** | SQL queries on Parquet |
| **EMR** | Big data processing |
| **Lake Formation** | Data lake management |

## Usage

### Load Account Data
```python
import pandas as pd

accounts = pd.read_parquet('accounts.parquet')
print(accounts.head())
```

### Load Ledger Data
```python
ledger = pd.read_parquet('ledger.parquet')
print(ledger.head())
```

### Join Accounts with Ledger
```python
# Get all transactions for active accounts
active_accounts = accounts[accounts['account_status'] == 'ACTIVE']
transactions = ledger.merge(active_accounts, on='account_id')
```

### Calculate Account Summary
```python
# Total debits and credits per account
summary = ledger.groupby('account_id').agg({
    'debit_amount': 'sum',
    'credit_amount': 'sum',
    'balance': 'last'
})
```

### Find High-Value Transactions
```python
# Transactions over ₹1 lakh
high_value = ledger[
    (ledger['debit_amount'] > 100000) | 
    (ledger['credit_amount'] > 100000)
]
```

## Data Characteristics

- **ACID Compliant**: Atomicity, Consistency, Isolation, Durability
- **Double-Entry**: Every debit has corresponding credit
- **Immutable**: Ledger entries cannot be modified
- **Auditable**: Complete transaction trail
- **Partitionable**: Can partition by date/account for performance

## Sample Data

### Account Record
```
account_id: ACC00000001
account_number: 1234567890
account_type: SAVINGS
current_balance: ₹5,04,283
status: ACTIVE
```

### Ledger Entry
```
entry_id: LED0000000001
account_id: ACC00000001
transaction_type: DEPOSIT
credit_amount: ₹10,000
balance: ₹5,14,283
description: Cash Deposit
```

## AI/ML Applications

- **Credit Risk Scoring**: Predict default probability
- **Loan Approval Models**: Automated lending decisions
- **Fraud Detection**: Identify suspicious patterns
- **Balance Forecasting**: Predict future balances
- **Customer Segmentation**: Group by behavior

## Notes

- Synthetic data generated with realistic patterns
- Follows banking industry standards
- Suitable for testing and development
- ACID-compliant structure
- All amounts in Indian Rupees (₹)

## License

Synthetic dataset for educational and research purposes.
