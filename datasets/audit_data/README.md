# Audit Logs & Compliance Data

## Overview
Audit risk assessment data containing sector scores, risk parameters, and compliance metrics. Used for automated compliance monitoring and risk evaluation in financial auditing systems.

## Dataset Details

- **Total Records**: 776
- **Source**: Kaggle - Audit Risk Dataset
- **Format**: CSV, Parquet
- **Data Type**: Audit findings with risk scores

## Data Schema

| Column | Type | Description |
|--------|------|-------------|
| Sector_score | float | Sector risk score |
| LOCATION_ID | integer | Location identifier |
| PARA_A | float | Parameter A value |
| Score_A | float | Score for parameter A |
| Risk_A | float | Risk score A |
| PARA_B | float | Parameter B value |
| Score_B | float | Score for parameter B |
| Risk_B | float | Risk score B |
| TOTAL | float | Total score |
| numbers | integer | Number count |
| Risk_C | float | Risk score C |
| Money_Value | float | Monetary value |
| Score_MV | float | Money value score |
| Risk_D | float | Risk score D |
| District_Loss | integer | District loss indicator |
| PROB | float | Probability score |
| RiSk_E | float | Risk score E |
| History | integer | Historical indicator |
| Prob | float | Probability value |
| Risk_F | float | Risk score F |
| Score | float | Overall score |
| Inherent_Risk | float | Inherent risk score |
| CONTROL_RISK | float | Control risk score |
| Detection_Risk | float | Detection risk score |
| Audit_Risk | float | Overall audit risk |
| Risk | integer | Risk flag (0 = low, 1 = high) |

## Use Cases

### Automated Compliance Monitoring
- Real-time risk assessment
- Compliance violation detection
- Regulatory reporting

### Risk Scoring
- Calculate audit risk scores
- Identify high-risk areas
- Prioritize audit activities

### Fraud Detection
- Anomaly detection in audit trails
- Pattern recognition
- Suspicious activity flagging

### SOX Compliance
- Sarbanes-Oxley Act compliance
- Internal control testing
- Financial reporting accuracy

## Industry Standards

- **SOX** - Sarbanes-Oxley Act
- **ISO 27001** - Information security management
- **Basel III** - Banking supervision
- **COSO Framework** - Internal control framework

## AWS Services Integration

| Service | Purpose |
|---------|---------|
| **CloudWatch** | Log monitoring and alerts |
| **S3** | Immutable audit log storage |
| **Lake Formation** | Data lake for compliance data |
| **Glue** | ETL for audit data processing |
| **Athena** | SQL queries on audit logs |
| **CloudTrail** | AWS API audit trails |
| **Config** | Resource compliance tracking |
| **Macie** | Sensitive data discovery |

## File Formats

### CSV (Batch)
- **File**: audit_data.csv
- **Use**: Batch compliance reports
- **Protocol**: Syslog, Batch ETL

### Parquet (Analytics)
- **Use**: Long-term retention and analysis
- **Optimized for**: Athena, Redshift
- **Compression**: Snappy

### JSON (Streaming)
- **Use**: Real-time audit logs
- **Protocol**: Kafka, Syslog
- **Format**: Line-delimited JSON

## Usage

### Load Data
```python
import pandas as pd

audit = pd.read_csv('audit_data.csv')
print(audit.head())
```

### High-Risk Audits
```python
high_risk = audit[audit['Risk'] == 1]
print(f"High-risk audits: {len(high_risk)}")
```

### Risk Distribution
```python
risk_summary = audit.groupby('Risk').agg({
    'Audit_Risk': 'mean',
    'Inherent_Risk': 'mean',
    'CONTROL_RISK': 'mean'
})
print(risk_summary)
```

### Location-Based Analysis
```python
location_risk = audit.groupby('LOCATION_ID')['Risk'].mean()
high_risk_locations = location_risk[location_risk > 0.5]
```

## Data Characteristics

- **Immutable**: Audit logs cannot be modified
- **Long-term Retention**: Stored for 7+ years
- **Time-series**: Chronological audit trail
- **Compliance-focused**: Regulatory requirements
- **Risk-scored**: Multiple risk dimensions

## Sample Record

```
Sector_score: 3.89
LOCATION_ID: 23
Inherent_Risk: 8.574
CONTROL_RISK: 0.4
Detection_Risk: 0.5
Audit_Risk: 1.7148
Risk: 1 (High Risk)
```

## Risk Calculation

```
Audit Risk = Inherent Risk × Control Risk × Detection Risk
```

## Statistics

- **High-Risk Records**: ~40%
- **Low-Risk Records**: ~60%
- **Avg Audit Risk**: 1.5
- **Avg Inherent Risk**: 8.0
- **Avg Control Risk**: 0.4

## AI/ML Applications

- **Risk Prediction**: Classification models
- **Anomaly Detection**: Unsupervised learning
- **Compliance Automation**: Rule-based systems
- **Fraud Detection**: Pattern recognition
- **Audit Planning**: Optimization algorithms

## Data Processing Pipeline

```
Audit Logs → Kafka → S3 → Glue ETL → Parquet → Athena → QuickSight
```

## Compliance Requirements

- **Retention**: 7 years minimum
- **Immutability**: Write-once, read-many
- **Encryption**: At-rest and in-transit
- **Access Control**: Role-based permissions
- **Audit Trail**: Track all access

## Notes

- Real audit risk assessment data
- Multiple risk dimensions
- Suitable for compliance testing
- Immutable storage required
- Long-term retention needed

## License

Public dataset from Kaggle. For educational and research purposes.
