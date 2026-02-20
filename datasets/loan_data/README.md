# Loan & Credit Data

## Overview
Real loan application dataset containing applicant information, loan details, and approval status. Used for credit risk modeling and loan default prediction in banking systems.

## Dataset Details

- **Total Records**: 614
- **Source**: Kaggle - Loan Prediction Dataset
- **Format**: CSV, Parquet
- **Data Type**: Loan applications with approval status

## Data Schema

| Column | Type | Description |
|--------|------|-------------|
| Loan_ID | string | Unique loan application ID (LP001002) |
| Gender | string | Male, Female |
| Married | string | Yes, No |
| Dependents | string | Number of dependents (0, 1, 2, 3+) |
| Education | string | Graduate, Not Graduate |
| Self_Employed | string | Yes, No |
| ApplicantIncome | integer | Applicant's monthly income |
| CoapplicantIncome | integer | Co-applicant's monthly income |
| LoanAmount | float | Loan amount in thousands |
| Loan_Amount_Term | integer | Loan term in months (360 = 30 years) |
| Credit_History | integer | 1 = good credit, 0 = bad credit |
| Property_Area | string | Urban, Semiurban, Rural |
| Loan_Status | string | Y = Approved, N = Rejected |

## Use Cases

### Default Prediction
- Predict loan default probability
- Risk assessment models
- Credit scoring algorithms

### Loan Approval Automation
- Automated lending decisions
- Rule-based approval systems
- ML-powered underwriting

### Credit Risk Modeling
- Calculate risk scores
- Portfolio risk analysis
- Basel III compliance

### Historical Behavior Analysis
- Approval rate trends
- Default rate by segment
- Income vs loan amount patterns

## Industry Standards

- **Basel III** - Banking supervision regulations
- **FICO Standards** - Credit scoring methodology
- **Fair Lending** - Equal Credit Opportunity Act
- **Risk Management** - Credit risk assessment

## AWS Services Integration

| Service | Purpose |
|---------|---------|
| **Glue** | ETL processing and data cataloging |
| **Athena** | SQL queries on loan data |
| **Redshift** | Data warehouse for analytics |
| **SageMaker** | ML models for default prediction |
| **S3** | Store historical loan data |
| **QuickSight** | Loan approval dashboards |

## File Formats

### CSV (Batch Processing)
- **File**: loan_data_set.csv
- **Use**: Batch ETL jobs
- **Protocol**: REST, Batch ETL

### Parquet (Analytics)
- **Use**: Data warehouse queries
- **Optimized for**: Athena, Redshift Spectrum
- **Compression**: Snappy

## Usage

### Load Data
```python
import pandas as pd

loans = pd.read_csv('loan_data_set.csv')
print(loans.head())
```

### Approval Rate
```python
approval_rate = (loans['Loan_Status'] == 'Y').mean() * 100
print(f"Approval Rate: {approval_rate:.2f}%")
```

### Default Risk by Credit History
```python
risk_analysis = loans.groupby('Credit_History')['Loan_Status'].value_counts(normalize=True)
print(risk_analysis)
```

### Income Analysis
```python
loans['TotalIncome'] = loans['ApplicantIncome'] + loans['CoapplicantIncome']
high_income = loans[loans['TotalIncome'] > 10000]
```

## Data Characteristics

- **Historical Data**: Past loan applications
- **Batch Processing**: Suitable for ETL jobs
- **Imbalanced**: More approvals than rejections
- **Missing Values**: Some loan amounts missing
- **Real Patterns**: Actual lending behavior

## Sample Records

```
Loan_ID: LP001002
Gender: Male
Married: No
ApplicantIncome: 5849
LoanAmount: Not specified
Credit_History: 1 (Good)
Property_Area: Urban
Loan_Status: Y (Approved)

Loan_ID: LP001003
Gender: Male
Married: Yes
ApplicantIncome: 4583
CoapplicantIncome: 1508
LoanAmount: 128 (thousands)
Credit_History: 1 (Good)
Property_Area: Rural
Loan_Status: N (Rejected)
```

## Statistics

- **Approval Rate**: ~68%
- **Rejection Rate**: ~32%
- **Avg Loan Amount**: ~140K
- **Avg Applicant Income**: ~5,400/month
- **Good Credit History**: ~85%

## AI/ML Applications

- **Default Prediction**: Binary classification
- **Credit Scoring**: Risk score calculation
- **Loan Amount Prediction**: Regression models
- **Approval Automation**: Decision trees
- **Risk Segmentation**: Clustering

## Data Processing Pipeline

```
CSV → AWS S3 → Glue ETL → Parquet → Redshift → SageMaker
```

## Notes

- Real loan application data
- Suitable for ML model training
- Missing values need imputation
- Imbalanced dataset (handle with SMOTE)
- Historical behavior patterns

## License

Public dataset from Kaggle. For educational and research purposes.
