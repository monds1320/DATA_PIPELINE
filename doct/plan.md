# Finance Data Pipeline Project Plan

## Part 0: Data Acquisition
- Download Finance real datasets
- Identify data sources and formats
- Establish data ingestion schedules

### AWS Services for Dataset Loading:

**1. Raw Data Storage:**
- **AWS S3**: Primary storage for all raw datasets
  - Bucket structure: `s3://finance-data-lake/raw/`
  - Folders by data type:
    - `market_data/` - Stock prices (CSV, Parquet)
    - `customer_kyc_data/` - KYC profiles (CSV, JSON)
    - `transaction_data/` - Bank transactions (XLSX, JSON, Parquet)
    - `account_ledger_data/` - Accounts & Ledger (Parquet)
    - `loan_data/` - Loan applications (CSV)
    - `audit_data/` - Audit logs (CSV)
    - `trade_orders_data/` - Trade orders (JSON, Parquet)

**2. Data Upload Methods:**
- **AWS CLI**: `aws s3 cp /local/path s3://bucket/path --recursive`
- **AWS SDK (Boto3)**: Python script for automated uploads
- **AWS DataSync**: Automated sync from local to S3
- **AWS Transfer Family**: SFTP/FTP uploads

**3. Data Cataloging:**
- **AWS Glue Crawler**: Auto-discover schemas and create catalog
- **AWS Glue Data Catalog**: Metadata repository for all datasets

**4. Data Format Optimization:**
- **AWS Glue ETL**: Convert CSV/XLSX → Parquet/ORC
- **AWS EMR**: Large-scale format conversions

**5. Data Organization:**
- **AWS Lake Formation**: Organize data lake structure
- **S3 Lifecycle Policies**: Archive old data to Glacier
- **S3 Versioning**: Track data changes

## Part 1: Data Sources
- **AWS S3**: Object storage for raw data
- **Firebase**: Real-time database
- **Azure**: Cloud storage and services
- **Google Drive**: File storage
- **Databases**: Relational/NoSQL databases

## Part 2: Data Extraction & Processing
- **AWS Glue**: Serverless ETL service
- **Local Python**: Custom processing scripts
- Data ingestion pipelines
- Format standardization

## Part 3: Data Processing Pipeline
1. **Data Profiling**: Analyze data quality and structure
2. **Deduplication**: Remove duplicate records
3. **PII Masking**: Anonymize sensitive information
4. **ETL**: Extract, Transform, Load operations
5. **Data Quality (DQ)**: Validation and cleansing

## Part 4: Data Warehouse Implementation
- **Platform**: Databricks / Snowflake
- **Structure**: Catalog → Database → Tables
- Data modeling and schema design
- Performance optimization

## Part 5: Data Governance
- Data lineage tracking
- Access controls and permissions
- Compliance and audit trails
- Data classification and tagging
- Metadata management

## Part 6: Data Consumers
- **Consumer 1 - ML**: Machine Learning models and analytics
- **Consumer 2 - BI**: Query-enabled dashboards and reporting
- API endpoints for data access
- Real-time and batch data delivery