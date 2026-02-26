# Databricks Data Warehouse Setup - AWS Quickstart Console Guide

## Overview
Step-by-step console guide using Databricks AWS Quickstart feature to create catalog, database, and table with S3 connection.

## Prerequisites
- **Databricks Token**: `YOUR_DATABRICKS_TOKEN_HERE`
- **S3 Bucket**: `tanmayrawtest101`
- **Data Path**: `fin_work/process_data/trade_orders/final_output_clean/final_processed_data.parquet/`
- **Records**: 874 trade orders

---

## Step 1: Create Catalog (SQL Editor)

### 1.1 Open Databricks SQL Editor
1. Go to: https://dbc-dp-1444828305810485.cloud.databricks.com
2. Click **SQL Editor** in left sidebar
3. Create new query

### 1.2 Create Catalog
Run this SQL command:
```sql
CREATE CATALOG IF NOT EXISTS trade_orders_catalog
COMMENT 'Trade orders data warehouse catalog';
```

### 1.3 Verify Catalog
```sql
SHOW CATALOGS;
```
✅ Should see `trade_orders_catalog` in the list

---

## Step 2: Create Database (SQL Editor)

### 2.1 Create Database
Run this SQL command:
```sql
CREATE DATABASE IF NOT EXISTS trade_orders_catalog.trade_orders_warehouse
COMMENT 'Trade orders data warehouse database';
```

### 2.2 Verify Database
```sql
SHOW DATABASES IN trade_orders_catalog;
```
✅ Should see `trade_orders_warehouse` in the list

---

## Step 3: Create Table with AWS Quickstart

### 3.1 Navigate to Create Table
1. Click **Data** in left sidebar
2. Click **Create table**
3. Click **Add data**
4. Select **S3**

### 3.2 Create External Location
1. Click **Create a new external location**
2. Select **AWS Quickstart (Recommended)**
3. **Bucket name**: Enter `tanmayrawtest101`
4. Click **Generate new token** (or use existing)
5. **Token**: `<your-token>`
6. Click **Launch Quickstart**

---

## Step 4: AWS CloudFormation Setup (Automatic)

### 4.1 AWS Account Redirect
- You will be redirected to AWS Console
- AWS CloudFormation service will open
- Pre-filled template will load

### 4.2 CloudFormation Parameters
The following will be auto-populated:
- **Databricks Personal Access Token**: `<your-token>`
- **S3 Bucket Name**: `tanmayrawtest101`
- **Databricks Account ID**: Auto-detected
- **Workspace URL**: Auto-detected

### 4.3 CloudFormation Resources Created
The stack will create:
1. **IAM Role**: For Databricks S3 access
2. **IAM Policy**: S3 permissions for the bucket with the following policy:

```json
{
	"Version": "2012-10-17",
	"Statement": [
		{
			"Sid": "Statement1",
			"Effect": "Allow",
			"Action": [
				"s3:GetObject",
				"s3:GetObjectVersion",
				"s3:PutObject",
				"s3:DeleteObject",
				"s3:ListBucket",
				"s3:GetBucketLocation",
				"s3:ListBucketMultipartUploads",
				"s3:ListMultipartUploadParts",
				"s3:AbortMultipartUpload"
			],
			"Resource": [
				"arn:aws:s3:::tanmayrawtest101",
				"arn:aws:s3:::tanmayrawtest101/*",
				"arn:aws:s3:::databricks-s3-ingest-*",
				"arn:aws:s3:::databricks-s3-ingest-*/*"
			]
		},
		{
			"Sid": "Statement2",
			"Effect": "Allow",
			"Action": [
				"iam:CreateRole",
				"iam:DeleteRole",
				"iam:GetRole",
				"iam:AttachRolePolicy",
				"iam:DetachRolePolicy",
				"iam:DeleteRolePolicy",
				"iam:PutRolePolicy",
				"iam:GetRolePolicy",
				"iam:ListRolePolicies",
				"iam:ListAttachedRolePolicies",
				"iam:TagRole",
				"iam:UntagRole",
				"iam:PassRole",
				"iam:CreateInstanceProfile",
				"iam:DeleteInstanceProfile",
				"iam:GetInstanceProfile",
				"iam:AddRoleToInstanceProfile",
				"iam:RemoveRoleFromInstanceProfile",
				"lambda:*",
				"s3:CreateBucket",
				"s3:DeleteBucket"
			],
			"Resource": "*"
		}
	]
}
```

3. **Storage Credential**: In Databricks Unity Catalog
4. **External Location**: Linking S3 to Databricks

### 4.4 Create Stack
1. Review the parameters
2. Check **"I acknowledge that AWS CloudFormation might create IAM resources"**
3. Click **Create stack**
4. Wait for **CREATE_COMPLETE** status

---

## Step 5: Return to Databricks and Create Table

### 5.1 Connection Established
- Return to Databricks console
- External location should now be available
- S3 bucket connection is ready

### 5.2 Select S3 Data File
1. **External location**: Select the newly created location
2. **Browse files**: Navigate to `fin_work/process_data/trade_orders/final_output_clean/`
3. **Select file**: `final_processed_data.parquet`
4. **File format**: Parquet (auto-detected)
5. Click **Preview data**

### 5.3 Verify Data Preview
Should display:
- ✅ **874 rows** detected
- ✅ Columns: order_id, customer_id, order_date, order_status, order_price, etc.
- ✅ Sample data preview

### 5.4 Configure Table
1. **Catalog**: Select `trade_orders_catalog`
2. **Database**: Select `trade_orders_warehouse`
3. **Table name**: `trade_orders`
4. **Table type**: External table
5. **Comment**: `Trade orders fact table - 874 records`

### 5.5 Create Table
1. Review schema (adjust column types if needed)
2. Click **Create table**
3. Wait for creation to complete
4. ✅ **Table created successfully**

---

## Step 6: Verify Data Warehouse

### 6.1 Test Queries (SQL Editor)

**Count total records:**
```sql
SELECT COUNT(*) as total_records 
FROM trade_orders_catalog.trade_orders_warehouse.trade_orders;
```
**Expected result**: 874

**Sample data:**
```sql
SELECT * 
FROM trade_orders_catalog.trade_orders_warehouse.trade_orders 
LIMIT 5;
```

**Order status summary:**
```sql
SELECT 
    order_status,
    COUNT(*) as count,
    ROUND(AVG(order_price), 2) as avg_price
FROM trade_orders_catalog.trade_orders_warehouse.trade_orders
GROUP BY order_status
ORDER BY count DESC;
```

---

## Final Result ✅

**Complete Data Warehouse:**
- **Catalog**: `trade_orders_catalog` (created via SQL)
- **Database**: `trade_orders_warehouse` (created via SQL)
- **Table**: `trade_orders` (created via AWS Quickstart)
- **Full Path**: `trade_orders_catalog.trade_orders_warehouse.trade_orders`
- **Records**: 874 trade orders
- **Connection**: S3 via AWS Quickstart CloudFormation

**AWS Infrastructure (Auto-created):**
- ✅ CloudFormation stack deployed
- ✅ IAM role with S3 access policy
- ✅ Storage credential in Unity Catalog
- ✅ External location connected to S3
- ✅ Secure connection established

**Databricks Structure:**
- ✅ Unity Catalog enabled
- ✅ Catalog and database created
- ✅ External table populated with data
- ✅ Ready for analytics and reporting

Your Databricks data warehouse is now ready with the AWS Quickstart automated connection!