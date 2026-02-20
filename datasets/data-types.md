# Finance Data Types Overview

| Data Type | Data Format | Protocols | Industry Standards | AWS Services | Healthcare Systems / Operations | Additional Info | AI Agent Use in Business Operations |
|-----------|-------------|-----------|-------------------|--------------|--------------------------------|-----------------|-----------------------------------|
| Transaction Data (Payments, Transfers, Card Swipes) | JSON (streaming), Avro, Parquet | ISO 20022, REST, Kafka | PCI-DSS, AML, KYC | MSK, S3, Glue, EMR | Payment Gateway, Core Banking | High-volume, low-latency, partitioned by date/user | Real-time Fraud Detection, Risk Scoring |
| Market Data (Stocks, FX, Crypto Prices) | JSON (tick data), CSV (EOD), Parquet | FIX Protocol, WebSockets | MiFID II, SEC Regulations | Kinesis, EMR, Redshift | Trading Engine, Market Data Platform | Millisecond ingestion, time-series optimized | Trade Anomaly Detection, Price Forecasting |
| Customer Data (KYC, Profiles) | JSON, CSV, ORC | REST APIs, gRPC | GDPR, SOC 2 | RDS, DynamoDB, IAM | CRM System, KYC Verification | PII data, encryption required | Customer Segmentation, Churn Prediction |
| Account & Ledger Data | Parquet, ORC, Avro | SWIFT, ISO 8583 | Basel III, SOX | Aurora, S3, Glue | Ledger System, Settlement System | ACID compliance required | Credit Risk Modeling, Loan Approval |
| Loan & Credit Data | CSV (batch), Parquet | REST, Batch ETL | Basel III, FICO Standards | Glue, Athena, Redshift | Loan Management System | Historical behavior analysis | Default Prediction, Credit Scoring |
| Audit Logs & Compliance Data | JSON, Log format, Parquet | Kafka, Syslog | SOX, ISO 27001 | CloudWatch, S3, Lake Formation | Compliance Monitoring System | Immutable storage, long-term retention | Automated Compliance Monitoring |
| Trade Orders & Execution Data | Avro, JSON, Parquet | FIX, Kafka | SEC, FINRA | MSK, EMR, Snowflake | Trading Platform | High-frequency event stream | Algorithmic Trading Optimization |