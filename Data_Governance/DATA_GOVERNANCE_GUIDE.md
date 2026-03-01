# Cross-Databricks Data Sharing Guide

## Overview
Share filtered data across Databricks accounts using Delta Sharing with column and row-level filtering.

---

## Prerequisites

### Required
- Databricks workspace with Unity Catalog enabled
- SQL Warehouse ID
- Personal Access Token
- **External Delta Sharing enabled** (contact support@databricks.com)
- **IMPORTANT**: External Delta Sharing requires Premium or Enterprise tier
  - NOT available on Free Trial or Community Edition
  - Contact Databricks support to upgrade if needed

### Python Dependencies
```bash
pip install requests
```

---

## Quick Start

### 1. Run the Script
```bash
python cross_databricks_sharing.py
```

### 2. Configuration (Default Values Available)
```
Workspace URL [https://dbc-f30c6cd6-abcb.cloud.databricks.com]: <press Enter>
Warehouse ID [8e650ab1879dac31]: <press Enter>
Token: ********** (masked input)
```

### 3. Select Data to Share
```
Available Catalogs:
1. market_data_catalog
2. sales_catalog

Select catalog: 1

Available Schemas:
1. market_data_dw
2. raw_data

Select schema: 1

Available Tables:
1. final_processed_data
2. stock_prices

Select table: 1
```

### 4. Choose Filtering Options
```
Filter Options:
1. Full table (no filtering)
2. Column filtering only
3. Row filtering only
4. Column + Row filtering

Choice (1-4): 4
```

### 5. Select or Create Table
```
Existing Tables:
1. final_processed_data
2. dev_ml
3. Create new table

Select table or create new: 3

Table name for filtered data: ml_training_data
```

### 6. Apply Column Filtering
```
Available columns:
1. symbol
2. date
3. open
4. high
5. low
6. close
7. volume
8. intraday_range
9. volume_category
10. year
...

Select columns (comma-separated numbers or 'all'): 1,2,3,4,5,6,7,8,9,14,17,20
```

### 7. Apply Row Filtering
```
Row Filter Examples:
  - year >= 2023
  - status = 'active' AND date >= '2024-01-01'
  - amount > 1000

Enter row filter: year >= 2023
```

### 8. Create or Select Share
```
Existing Shares:
1. dev_ml
2. ml_dev
3. Create new share

Select share or create new: 3

Share name: saurabh_ml_share
```

---

## Filtering Options Explained

### Option 1: Full Table (No Filtering)
- Shares complete table as-is
- All columns and rows included
- Use for trusted partners with full access needs

### Option 2: Column Filtering Only
- Select specific columns to share
- Hide sensitive columns (PII, internal data)
- Example: Hide SSN, salary, credit card columns

**Use Case**: Share customer data but hide payment information
```
Columns to share: customer_id, name, email, country
Hidden columns: ssn, credit_card, bank_account
```

### Option 3: Row Filtering Only
- Filter rows based on SQL WHERE clause
- All columns included
- Example: Share only recent data or specific regions

**Use Case**: Share only US region data
```
Row filter: region = 'US'
```

### Option 4: Column + Row Filtering (Recommended)
- Combines both filtering methods
- Maximum data security
- Minimize data exposure

**Use Case**: Share ML training data with specific features and time range
```
Columns: 1,2,3,4,5,6,7,8,9,14,17,20
Row filter: year >= 2023
```

---

## Row Filter Examples

### Date Filters
```sql
-- Recent data only
year >= 2023
date >= '2024-01-01'
created_at >= CURRENT_DATE - INTERVAL 30 DAYS

-- Date range
date BETWEEN '2023-01-01' AND '2023-12-31'
```

### Status Filters
```sql
-- Active records only
status = 'active'
is_deleted = false

-- Multiple statuses
status IN ('active', 'pending', 'verified')
```

### Regional Filters
```sql
-- Single region
region = 'US'
country = 'United States'

-- Multiple regions
region IN ('US', 'CA', 'UK')
country IN ('United States', 'Canada', 'United Kingdom')
```

### Numeric Filters
```sql
-- Threshold
amount > 1000
quantity >= 100

-- Range
amount BETWEEN 1000 AND 5000
age >= 18 AND age <= 65
```

### Combined Filters
```sql
-- Complex conditions
region = 'US' AND status = 'active' AND amount > 1000
(country = 'US' OR country = 'CA') AND year >= 2023
status IN ('active', 'verified') AND created_date >= '2024-01-01'
```

---

## Manual Sharing Steps (UI)

### When API Fails
If the script shows "API share creation failed", follow these manual steps:

#### 1. Add Tables to Share
```
1. Go to Databricks UI > Data Explorer
2. Click 'Delta Sharing' > 'Shared by me'
3. Select your share (e.g., 'saurabh_ml_share')
4. Click 'Add assets'
5. Select tables created by script
6. Click 'Add'
```

#### 2. Create Recipient

**CRITICAL**: External Delta Sharing must be enabled first.

**If Not Enabled**:
```
Contact: support@databricks.com
Subject: Enable External Delta Sharing on Metastore
Message: "I need External Delta Sharing enabled on my metastore 
         for cross-account data sharing"
Provide: 
  - Account email: tanmaymondal1320@gmail.com
  - Workspace URL: https://dbc-f30c6cd6-abcb.cloud.databricks.com
  - Current tier: [Free Trial / Standard / Premium / Enterprise]
  
NOTE: External Delta Sharing requires Premium or Enterprise tier.
      Free Trial and Community Edition accounts are NOT supported.
      You may need to upgrade your account.
```

**After Enabled**:
```
1. Click 'Create recipient'
2. Recipient name: saurabh
3. Recipient type: 
   - Databricks: For Databricks-to-Databricks sharing
     (Requires recipient's metastore ID)
   - Open: For external platforms
     (Generates credential file)
4. Click 'Create'
```

#### 3. Grant Permissions
```
1. Select recipient
2. Click 'Grant permissions'
3. Select 'SELECT' permission
4. Click 'Grant'
```

#### 4. Share Activation
```
1. Copy activation URL or download credential file
2. Send to recipient securely
```

---

## Recipient Setup

### For Databricks Recipients

#### 1. Get Metastore ID
```sql
-- Run in recipient's workspace
SELECT current_metastore();
-- Output: aws:us-east-2:a6874015-a1ae-4046-86bb-7b34d9a0fc26
-- Share this with provider
```

#### 2. Accept Share
```
1. Receive activation URL from provider
2. Go to Catalog > Delta Sharing > Shared with me
3. Click 'Create catalog from share'
4. Paste activation URL
5. Catalog name: provider_shared_data
6. Click 'Create'
```

#### 3. Query Shared Data
```sql
-- List tables
SHOW TABLES IN provider_shared_data.market_data_dw;

-- Query data
SELECT * FROM provider_shared_data.market_data_dw.ml_training_data
WHERE symbol = 'AAPL'
LIMIT 10;

-- Check data range
SELECT 
    MIN(date) as start_date,
    MAX(date) as end_date,
    COUNT(*) as total_rows
FROM provider_shared_data.market_data_dw.ml_training_data;
```

---

## Use Cases

### Use Case 1: ML Training Data Sharing
**Scenario**: Share filtered stock market data for ML model training

**Configuration**:
```
Table: market_data_catalog.market_data_dw.final_processed_data
Columns: symbol, date, open, high, low, close, volume, 
         intraday_range, volume_category, is_positive_daily_return,
         is_positive_price_change, is_positive_price_change_pct
Row Filter: year >= 2023
Output Table: ml_training_data
```

**Result**: Recipient gets clean ML features without sensitive internal columns

### Use Case 2: Partner Analytics
**Scenario**: Share sales data with business partner

**Configuration**:
```
Table: sales_catalog.sales_db.orders
Columns: order_id, product_id, quantity, amount, region, order_date
         (Hide: customer_ssn, credit_card, internal_notes)
Row Filter: region IN ('US', 'CA') AND status = 'completed'
Output Table: partner_sales_data
```

**Result**: Partner sees completed orders for their regions only

### Use Case 3: Compliance Reporting
**Scenario**: Share data with auditors

**Configuration**:
```
Table: finance_catalog.finance_db.transactions
Columns: transaction_id, date, amount, category, status
         (Hide: user_id, account_number, routing_number)
Row Filter: date >= '2024-01-01' AND status = 'completed'
Output Table: audit_transactions
```

**Result**: Auditors get transaction data without PII

---

## Security Best Practices

### 1. Column Filtering
**Always Hide**:
- PII: SSN, credit card, phone, email
- Financial: Bank account, routing number, salary
- Internal: Internal notes, cost price, margin
- Audit: Created by, updated by (unless needed)

### 2. Row Filtering
**Common Patterns**:
- **Regional**: `region = 'US'` (GDPR compliance)
- **Temporal**: `year >= 2023` (recent data only)
- **Status**: `status = 'active'` (exclude deleted/inactive)
- **Tier**: `customer_tier = 'premium'` (segment data)

### 3. Combined Approach
**Best Practice**: Use both column and row filtering
```
✓ Hide sensitive columns
✓ Filter to relevant data subset
✓ Minimize data exposure
✓ Document filtering logic
```

---

## Troubleshooting

### Issue: "External Delta Sharing not enabled"
**Solution**: 
- Contact support@databricks.com to enable it on your metastore
- **IMPORTANT**: Requires Premium or Enterprise tier
- Free Trial and Community Edition are NOT supported
- You may need to upgrade your Databricks account

### Issue: "API Error: No API found for POST /unity-catalog/shares"
**Solution**: Your workspace has API restrictions. Use manual UI steps provided by script

### Issue: "Only table in Delta Lake format can be added to a share"
**Solution**: Script creates Delta tables (not views). Ensure table was created successfully

### Issue: "Column not found"
**Solution**: Verify column names with `DESCRIBE TABLE catalog.schema.table`

### Issue: "Invalid row filter"
**Solution**: Test filter in SQL Editor first:
```sql
SELECT * FROM catalog.schema.table WHERE your_filter LIMIT 10;
```

### Issue: "View creation failed"
**Solution**: 
- Check warehouse ID is correct
- Ensure warehouse is running
- Verify you have CREATE TABLE permission

---

## Script Features

### 1. Masked Token Input
- Shows asterisks while typing
- Secure token entry
- Character count displayed

### 2. Default Configuration
- Workspace URL: Pre-filled
- Warehouse ID: Pre-filled
- Press Enter to use defaults

### 3. Interactive Selection
- Numbered catalog/schema/table selection
- Browse existing tables
- Reuse existing tables or create new

### 4. Existing Resource Reuse
- Select existing shares
- Select existing tables
- Avoid duplicates

### 5. Error Handling
- API error messages displayed
- Fallback to manual UI instructions
- Clear troubleshooting guidance

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│         Provider Account (Your Workspace)                    │
│         Requires: Premium or Enterprise Tier                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Unity Catalog                                          │ │
│  │  ├─ Catalog: market_data_catalog                      │ │
│  │  │   └─ Schema: market_data_dw                        │ │
│  │  │       ├─ Table: final_processed_data (source)      │ │
│  │  │       └─ Table: ml_training_data (filtered)        │ │
│  │  │                                                     │ │
│  │  └─ Share: saurabh_ml_share                             │ │
│  │      └─ Table: ml_training_data                       │ │
│  │          (Columns: 12 selected)                       │ │
│  │          (Rows: year >= 2023)                         │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Delta Sharing Protocol
                            │ (Requires External Delta Sharing)
                            │ (Activation URL / Credential File)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│         Recipient Account (Saurabh's Workspace)              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Unity Catalog                                          │ │
│  │  └─ Catalog: provider_shared_data                     │ │
│  │      └─ Schema: market_data_dw                        │ │
│  │          └─ Table: ml_training_data (read-only)       │ │
│  │              (Filtered data from provider)            │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

Note: External Delta Sharing NOT available on Free Trial or Community Edition
```

---

## Cost Implications

### Provider Account
- **Tier Requirement**: Premium or Enterprise tier (NOT Free Trial/Community Edition)
- **Storage**: Standard Unity Catalog storage for filtered tables
- **Compute**: SQL Warehouse usage for table creation
- **External Delta Sharing**: Included in Premium/Enterprise tier (no additional feature cost)

### Recipient Account
- **Storage**: Metadata only (no data duplication)
- **Compute**: Pay for queries on shared data
- **Data Transfer**: FREE (Databricks-to-Databricks)

### Important Notes
- External Delta Sharing is NOT a separate paid add-on
- It's included in Premium/Enterprise tier but requires manual enablement by Databricks support
- Free Trial and Community Edition accounts cannot use this feature regardless of willingness to pay

---

## Monitoring

### Provider: Check Share Status
```sql
-- List all shares
SHOW SHARES;

-- Show tables in share
SHOW ALL IN SHARE saurabh_ml_share;

-- Check table details
DESCRIBE TABLE market_data_catalog.market_data_dw.ml_training_data;
```

### Recipient: Verify Access
```sql
-- List shared catalogs
SHOW CATALOGS;

-- Check table schema
DESCRIBE TABLE provider_shared_data.market_data_dw.ml_training_data;

-- Verify data
SELECT COUNT(*) FROM provider_shared_data.market_data_dw.ml_training_data;
```

---

## Quick Reference

### Script Workflow
```
1. Configure (URL, Warehouse, Token)
2. Select Catalog > Schema > Table
3. Choose Filtering (1-4)
4. Select/Create Table Name
5. Apply Column Filter (if selected)
6. Apply Row Filter (if selected)
7. Select/Create Share
8. Follow Manual UI Steps (if API fails)
```

### Key Commands
```bash
# Run script
python cross_databricks_sharing.py

# Get metastore ID (recipient)
SELECT current_metastore();

# Test row filter
SELECT * FROM catalog.schema.table WHERE filter LIMIT 10;

# Check table columns
DESCRIBE TABLE catalog.schema.table;
```

---

## Support

### Contact Databricks Support
- **Email**: support@databricks.com
- **Subject**: Enable External Delta Sharing on Metastore
- **Required Info**: Account email, Workspace URL, Use case

### Script Issues
- Check Python version (3.7+)
- Verify `requests` library installed
- Ensure token has required permissions
- Check warehouse is running

---

## Summary

This guide covers the complete workflow for cross-Databricks data sharing with filtering:

✓ Interactive script with default configurations
✓ Column and row-level filtering
✓ Existing resource reuse
✓ Manual UI fallback for API restrictions
✓ Complete recipient setup instructions
✓ Security best practices
✓ Troubleshooting guidance

**Remember**: 
- External Delta Sharing must be enabled by Databricks support before you can create recipients
- Requires Premium or Enterprise tier (NOT available on Free Trial or Community Edition)
- Contact support@databricks.com to check your account tier and enable the feature
