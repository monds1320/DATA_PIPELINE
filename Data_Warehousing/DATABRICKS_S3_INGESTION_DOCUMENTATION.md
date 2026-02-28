# Databricks S3 Streaming Ingestion - Technical Documentation

## Overview
Automated Python script to create Databricks external tables from S3 data sources using Unity Catalog and SQL Warehouse APIs.

---

## Script Information

**File**: `databricks_s3_streaming_ingestion.py`  
**Purpose**: Automate catalog, schema, and external table creation in Databricks  
**Language**: Python 3.x  
**Dependencies**: `requests`, `json`, `typing`

---

## Architecture

```
┌─────────────────┐
│   User Input    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│  Python Script  │─────▶│ Databricks APIs  │
└────────┬────────┘      └──────────────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│  Unity Catalog  │◀────▶│   S3 Storage     │
└─────────────────┘      └──────────────────┘
```

---

## Input Parameters

### 1. Configuration Inputs
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `workspace_url` | string | Yes | `https://dbc-f30c6cd6-abcb.cloud.databricks.com` | Databricks workspace URL |
| `token` | string | Yes | - | Personal access token |
| `warehouse_id` | string | Yes | `8e650ab1879dac31` | SQL warehouse ID |

### 2. S3 Location Inputs
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `external_location` | string | Yes | Selected from dropdown |
| `s3_folder` | string | Yes | S3 folder path (e.g., `fin_work/process_data/`) |

### 3. Table Configuration Inputs
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `catalog_name` | string | Yes | - | Catalog name |
| `schema_name` | string | Yes | - | Schema/database name |
| `table_name` | string | No | Auto-generated | Table name |
| `file_format` | string | Yes | `parquet` | File format (parquet/json/csv/delta) |
| `schedule` | string | No | `0 0 * * *` | Cron schedule (not used for external tables) |

---

## Class: DatabricksS3StreamingIngestion

### Constructor

```python
def __init__(self, workspace_url: str, token: str, warehouse_id: str = None)
```

**Purpose**: Initialize Databricks API client  
**Logic**:
- Store workspace URL, token, and warehouse ID
- Create authorization headers with Bearer token
- Strip trailing slashes from URL

**Headers Created**:
```json
{
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json"
}
```

---

## Functions & API Methods

### 1. list_external_locations()

**Purpose**: Fetch all S3 external locations from Unity Catalog

**API Call**:
- **Method**: `GET`
- **Endpoint**: `/api/2.1/unity-catalog/external-locations`
- **API Name**: Unity Catalog External Locations API

**Logic**:
1. Send GET request to external locations endpoint
2. Parse JSON response
3. Extract `external_locations` array
4. Return list of location dictionaries

**Response Structure**:
```json
{
  "external_locations": [
    {
      "name": "location_name",
      "url": "s3://bucket-name/",
      "credential_name": "credential_name"
    }
  ]
}
```

**Return**: `List[Dict]` - List of external location objects

---

### 2. display_external_locations()

**Purpose**: Display locations as dropdown and get user selection

**Logic**:
1. Call `list_external_locations()` to fetch locations
2. Display numbered list with name, URL, and credential
3. Prompt user for selection (1-N)
4. Validate input (integer within range)
5. Return selected location URL

**User Interaction**:
```
AVAILABLE S3 EXTERNAL LOCATIONS
1. location_name
   URL: s3://bucket/
   Credential: credential_name
   
Select location (1-2): 
```

**Return**: `Optional[str]` - Selected S3 URL or None

---

### 3. create_catalog()

**Purpose**: Create Unity Catalog if not exists

**API Calls**:

#### Check if exists:
- **Method**: `GET`
- **Endpoint**: `/api/2.1/unity-catalog/catalogs`
- **API Name**: Unity Catalog Catalogs API

#### Create catalog:
- **Method**: `POST`
- **Endpoint**: `/api/2.1/unity-catalog/catalogs`
- **API Name**: Unity Catalog Catalogs API

**Request Payload**:
```json
{
  "name": "catalog_name",
  "comment": "Auto-created catalog for catalog_name",
  "storage_root": "s3://bucket/catalogs/catalog_name"
}
```

**Logic**:
1. GET request to check if catalog exists
2. If exists, return True
3. If not exists, prepare payload with name, comment, and storage_root
4. POST request to create catalog
5. Return True if status 200/201, else False

**Return**: `bool` - Success status

---

### 4. create_schema()

**Purpose**: Create schema (database) in catalog if not exists

**API Calls**:

#### Check if exists:
- **Method**: `GET`
- **Endpoint**: `/api/2.1/unity-catalog/schemas?catalog_name={catalog}`
- **API Name**: Unity Catalog Schemas API

#### Create schema:
- **Method**: `POST`
- **Endpoint**: `/api/2.1/unity-catalog/schemas`
- **API Name**: Unity Catalog Schemas API

**Request Payload**:
```json
{
  "name": "schema_name",
  "catalog_name": "catalog_name",
  "comment": "Auto-created schema for schema_name"
}
```

**Logic**:
1. GET request with catalog_name parameter to check if schema exists
2. If exists, return True
3. If not exists, prepare payload with name, catalog_name, and comment
4. POST request to create schema
5. Return True if status 200/201, else False

**Return**: `bool` - Success status

---

### 5. create_streaming_table()

**Purpose**: Create external table pointing to S3 data

**API Calls**:

#### Check if table exists:
- **Method**: `GET`
- **Endpoint**: `/api/2.1/unity-catalog/tables/{catalog}.{schema}.{table}`
- **API Name**: Unity Catalog Tables API

#### Drop table (if updating):
- **Method**: `POST`
- **Endpoint**: `/api/2.0/sql/statements/`
- **API Name**: SQL Statements API
- **SQL**: `DROP TABLE IF EXISTS {full_table_name}`

#### Create table:
- **Method**: `POST`
- **Endpoint**: `/api/2.0/sql/statements/`
- **API Name**: SQL Statements API

**Request Payload**:
```json
{
  "statement": "CREATE TABLE IF NOT EXISTS catalog.schema.table USING PARQUET LOCATION 's3://bucket/path/'",
  "warehouse_id": "warehouse_id"
}
```

**SQL Generation Logic**:

**For Parquet**:
```sql
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.{table}
USING PARQUET
LOCATION '{s3_path}'
```

**For JSON**:
```sql
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.{table}
USING JSON
LOCATION '{s3_path}'
```

**For CSV**:
```sql
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.{table}
USING CSV
OPTIONS (header='true', inferSchema='true')
LOCATION '{s3_path}'
```

**For Delta**:
```sql
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.{table}
USING DELTA
LOCATION '{s3_path}'
```

**Logic**:
1. Check if table exists via Unity Catalog API
2. If exists, prompt user for update (y/n)
3. If update=yes, drop table using SQL Statements API
4. Generate CREATE TABLE SQL based on file format
5. Execute SQL via SQL Statements API with warehouse_id
6. Return True if status 200/201, else False

**Return**: `bool` - Success status

---

### 6. _get_warehouse_id()

**Purpose**: Get SQL warehouse ID (private method)

**API Call**:
- **Method**: `GET`
- **Endpoint**: `/api/2.0/sql/warehouses`
- **API Name**: SQL Warehouses API

**Logic**:
1. If warehouse_id provided in constructor, return it
2. Else, GET request to fetch all warehouses
3. Extract first warehouse from response
4. Return warehouse ID
5. Raise exception if no warehouse found

**Return**: `str` - Warehouse ID

---

## Main Function Flow

### Step-by-Step Execution

```
1. Display Configuration Options
   ├─ Default: dbc-f30c6cd6-abcb.cloud.databricks.com
   └─ Custom: User provides URL and HTTP path

2. Initialize Client
   └─ Create DatabricksS3StreamingIngestion instance

3. Select External Location
   ├─ API: GET /api/2.1/unity-catalog/external-locations
   └─ User selects from dropdown

4. Input S3 Folder Path
   └─ Combine with external location URL

5. Select File Format
   └─ Options: Parquet, JSON, CSV, Delta

6. Input Catalog/Schema/Table Names
   ├─ Catalog: User input
   ├─ Schema: User input
   └─ Table: User input or auto-generated

7. Select Schedule (not used)
   └─ Options: Hourly, Daily, 6-hourly, Custom

8. Create Resources
   ├─ Create Catalog
   │  ├─ API: GET /api/2.1/unity-catalog/catalogs
   │  └─ API: POST /api/2.1/unity-catalog/catalogs
   ├─ Create Schema
   │  ├─ API: GET /api/2.1/unity-catalog/schemas
   │  └─ API: POST /api/2.1/unity-catalog/schemas
   └─ Create Table
      ├─ API: GET /api/2.1/unity-catalog/tables/{catalog}.{schema}.{table}
      └─ API: POST /api/2.0/sql/statements/

9. Display Success Message
   └─ Show full table path and query example
```

---

## API Endpoints Summary

| API Name | Endpoint | Method | Purpose |
|----------|----------|--------|---------|
| Unity Catalog External Locations | `/api/2.1/unity-catalog/external-locations` | GET | List S3 connections |
| Unity Catalog Catalogs | `/api/2.1/unity-catalog/catalogs` | GET | Check catalog exists |
| Unity Catalog Catalogs | `/api/2.1/unity-catalog/catalogs` | POST | Create catalog |
| Unity Catalog Schemas | `/api/2.1/unity-catalog/schemas` | GET | Check schema exists |
| Unity Catalog Schemas | `/api/2.1/unity-catalog/schemas` | POST | Create schema |
| Unity Catalog Tables | `/api/2.1/unity-catalog/tables/{catalog}.{schema}.{table}` | GET | Check table exists |
| SQL Statements | `/api/2.0/sql/statements/` | POST | Execute SQL (DROP/CREATE) |
| SQL Warehouses | `/api/2.0/sql/warehouses` | GET | Get warehouse ID |

---

## Error Handling

### HTTP Status Codes
- **200/201**: Success
- **4xx**: Client error (invalid input, not found)
- **5xx**: Server error

### Error Messages
```python
# API Error
print(f"✗ Error creating catalog: {response.text}")

# No warehouse found
raise Exception("No SQL warehouse found. Please provide warehouse_id or create one first.")

# No external locations
print("No external locations found. Please create one first.")
```

---

## Usage Example

```bash
python databricks_s3_streaming_ingestion.py
```

**Sample Interaction**:
```
Use default configuration? (y/n, default=y): y
Enter Databricks token: dapi123456789

Select location (1-2): 2
✓ Selected: db_s3_external (s3://tanmayrawtest101/)

Enter S3 folder path: fin_work/process_data/market_data/final_output/
Full S3 path: s3://tanmayrawtest101/fin_work/process_data/market_data/final_output/

Select format (1-4, default=1): 1

Enter catalog name: market_data_catalog
Enter schema name: market_data_warehouse
Enter table name: [Press Enter for auto-generate]
Auto-generated table name: final_output

Select schedule (1-4, default=2): 2

Creating Resources...
✓ Created catalog 'market_data_catalog'
✓ Created schema 'market_data_warehouse'
✓ Created external table 'market_data_catalog.market_data_warehouse.final_output'

✓ SETUP COMPLETED SUCCESSFULLY!
```

---

## Cost Implications

### Databricks Charges
- **Catalog/Schema/Table Creation**: FREE (metadata only)
- **SQL Warehouse Usage**: ~$0.35/hour (2X-Small Serverless)
- **Query Execution**: Pay-per-second when running queries
- **Idle Time**: $0 (auto-stops after 10 minutes)

### AWS Charges
- **S3 Storage**: Standard S3 pricing
- **Data Transfer**: S3 to Databricks (same region = minimal)

---

## Security

### Authentication
- **Method**: Bearer Token
- **Header**: `Authorization: Bearer <token>`

### Permissions Required
- Unity Catalog: CREATE CATALOG, CREATE SCHEMA, CREATE TABLE
- SQL Warehouse: USE WAREHOUSE, EXECUTE STATEMENT
- S3: READ access via external location credential

---

## Limitations

1. **External Tables Only**: Creates external tables, not managed tables
2. **No Streaming**: Despite the name, creates static tables (not Delta Live Tables)
3. **Manual Refresh**: Data changes in S3 require manual table refresh
4. **Single Warehouse**: Uses one warehouse ID for all operations

---

## Future Enhancements

- [ ] Add Delta Live Tables support for true streaming
- [ ] Implement scheduled refresh jobs
- [ ] Add data quality checks
- [ ] Support for partitioned tables
- [ ] Batch table creation from config file
- [ ] Add logging and monitoring

---

## Troubleshooting

### Common Issues

**Issue**: "Metastore storage root URL does not exist"  
**Solution**: Script now auto-creates storage location at `s3://bucket/catalogs/{catalog_name}`

**Issue**: "No SQL warehouse found"  
**Solution**: Provide warehouse_id in constructor or create warehouse in Databricks UI

**Issue**: "No external locations found"  
**Solution**: Create external location in Databricks UI first (Data → External Locations)

**Issue**: Table creation fails  
**Solution**: Check S3 path exists and warehouse has permissions

---

## References

- [Databricks Unity Catalog API](https://docs.databricks.com/api/workspace/unitycatalog)
- [Databricks SQL Statements API](https://docs.databricks.com/api/workspace/statementexecution)
- [External Tables Documentation](https://docs.databricks.com/sql/language-manual/sql-ref-external-tables.html)
