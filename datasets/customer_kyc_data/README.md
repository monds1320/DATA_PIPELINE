# Customer KYC Data

## Overview
Synthetic Indian customer KYC (Know Your Customer) data with complete profile information including personal details, financial data, and account information. Compliant with GDPR and SOC 2 standards structure.

## Dataset Details

- **Total Records**: 7,581
- **Format**: CSV
- **Country**: India
- **Data Type**: Customer profiles with PII data

## Data Schema

| Column | Type | Description |
|--------|------|-------------|
| customer_id | string | Unique customer identifier (IND000001) |
| account_number | string | Bank account number (10 digits) |
| first_name | string | Customer first name |
| last_name | string | Customer last name |
| email | string | Email address |
| phone | string | Phone number (+91 format) |
| aadhaar | string | Aadhaar number (12 digits) |
| pan | string | PAN card number |
| date_of_birth | date | Date of birth (YYYY-MM-DD) |
| address | string | Residential address |
| city | string | City |
| state | string | State |
| pin_code | string | PIN code (6 digits) |
| country | string | Country (India) |
| occupation | string | Occupation/Job title |
| annual_income | integer | Annual income (₹) |
| marital_status | string | Single, Married, Divorced, Widowed |
| education | string | Education level |
| credit_score | integer | Credit score (550-900) |
| account_balance | float | Current account balance (₹) |
| credit_default | string | yes/no |
| housing_loan | string | yes/no |
| personal_loan | string | yes/no |
| kyc_status | string | VERIFIED, PENDING |
| account_type | string | SAVINGS, CURRENT, SALARY |
| account_opened_date | date | Account opening date |
| last_transaction_date | date | Last transaction date |

## Use Cases

### Customer Segmentation
- Group customers by income, age, location
- Identify high-value customers
- Target marketing campaigns

### Churn Prediction
- Analyze account activity patterns
- Predict customer attrition
- Retention strategies

### Credit Risk Assessment
- Evaluate creditworthiness
- Loan approval decisions
- Risk scoring models

### KYC Verification
- Identity verification workflows
- Compliance checks
- Document validation

## Industry Standards

- **GDPR** - General Data Protection Regulation
- **SOC 2** - Service Organization Control 2
- **RBI Guidelines** - Reserve Bank of India KYC norms
- **PII Protection** - Personally Identifiable Information security

## AWS Services Integration

| Service | Purpose |
|---------|---------|
| **RDS/Aurora** | Store customer profiles |
| **DynamoDB** | NoSQL storage for flexible schema |
| **IAM** | Access control and permissions |
| **KMS** | Encrypt PII data |
| **Macie** | Discover and protect sensitive data |
| **Cognito** | Customer authentication |

## Usage

### Load Data
```python
import pandas as pd

customers = pd.read_csv('kyc_customers.csv')
print(customers.head())
```

### Filter by KYC Status
```python
verified = customers[customers['kyc_status'] == 'VERIFIED']
print(f"Verified customers: {len(verified)}")
```

### High-Value Customers
```python
high_value = customers[customers['annual_income'] > 1000000]
print(high_value[['customer_id', 'first_name', 'annual_income']])
```

### Credit Risk Analysis
```python
risky = customers[
    (customers['credit_score'] < 650) | 
    (customers['credit_default'] == 'yes')
]
```

## Data Characteristics

- **PII Data**: Requires encryption and access control
- **Synthetic**: Generated data, not real customers
- **Realistic**: Follows Indian naming conventions and formats
- **Complete**: All KYC fields populated
- **Compliant**: Follows banking KYC standards

## Sample Record

```
customer_id: IND000001
name: Rajesh Patel
email: rajesh.patel251@gmail.com
phone: +917958682846
aadhaar: 3286 2679 9935
pan: CSNBA2535G
city: Mumbai
annual_income: ₹5,22,599
credit_score: 764
kyc_status: VERIFIED
```

## AI/ML Applications

- **Customer Segmentation**: Clustering algorithms
- **Churn Prediction**: Classification models
- **Credit Scoring**: Risk assessment models
- **Fraud Detection**: Anomaly detection
- **Personalization**: Recommendation systems

## Notes

- Synthetic data for testing/development
- All PII fields are fake but realistic
- Follows Indian data formats (Aadhaar, PAN, phone)
- Suitable for KYC workflow testing
- All amounts in Indian Rupees (₹)

## License

Synthetic dataset for educational and research purposes.
