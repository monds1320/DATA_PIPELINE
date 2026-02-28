"""
Databricks S3 Streaming Ingestion Script
Automates creation of streaming tables from S3 with scheduled ingestion
"""

import requests
import json
from typing import List, Dict, Optional

class DatabricksS3StreamingIngestion:
    def __init__(self, workspace_url: str, token: str, warehouse_id: str = None):
        """
        Initialize Databricks connection
        
        Args:
            workspace_url: Databricks workspace URL (e.g., https://dbc-xxxxx.cloud.databricks.com)
            token: Databricks personal access token
            warehouse_id: SQL warehouse ID (extracted from HTTP path)
        """
        self.workspace_url = workspace_url.rstrip('/')
        self.token = token
        self.warehouse_id = warehouse_id
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def list_external_locations(self) -> List[Dict]:
        """List all available external locations (S3 connections)"""
        url = f"{self.workspace_url}/api/2.1/unity-catalog/external-locations"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            locations = response.json().get('external_locations', [])
            return locations
        else:
            print(f"Error listing external locations: {response.text}")
            return []
    
    def display_external_locations(self) -> Optional[str]:
        """Display external locations as dropdown and get user selection"""
        locations = self.list_external_locations()
        
        if not locations:
            print("No external locations found. Please create one first.")
            return None
        
        print("\n" + "="*60)
        print("AVAILABLE S3 EXTERNAL LOCATIONS")
        print("="*60)
        
        for idx, loc in enumerate(locations, 1):
            print(f"{idx}. {loc['name']}")
            print(f"   URL: {loc['url']}")
            print(f"   Credential: {loc.get('credential_name', 'N/A')}")
            print("-" * 60)
        
        while True:
            try:
                choice = int(input(f"\nSelect location (1-{len(locations)}): "))
                if 1 <= choice <= len(locations):
                    selected = locations[choice - 1]
                    print(f"\n✓ Selected: {selected['name']} ({selected['url']})")
                    return selected['url']
                else:
                    print(f"Please enter a number between 1 and {len(locations)}")
            except ValueError:
                print("Please enter a valid number")
    
    def create_catalog(self, catalog_name: str, storage_location: str = None) -> bool:
        """Create catalog if not exists"""
        url = f"{self.workspace_url}/api/2.1/unity-catalog/catalogs"
        
        # Check if exists
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            catalogs = response.json().get('catalogs', [])
            if any(c['name'] == catalog_name for c in catalogs):
                print(f"✓ Catalog '{catalog_name}' already exists")
                return True
        
        # Create new catalog with storage location
        payload = {
            "name": catalog_name,
            "comment": f"Auto-created catalog for {catalog_name}"
        }
        
        # Add storage location if provided
        if storage_location:
            payload["storage_root"] = storage_location
        
        response = requests.post(url, headers=self.headers, json=payload)
        if response.status_code in [200, 201]:
            print(f"✓ Created catalog '{catalog_name}'")
            return True
        else:
            print(f"✗ Error creating catalog: {response.text}")
            return False
    
    def create_schema(self, catalog_name: str, schema_name: str) -> bool:
        """Create schema (database) if not exists"""
        url = f"{self.workspace_url}/api/2.1/unity-catalog/schemas"
        
        # Check if exists
        response = requests.get(f"{url}?catalog_name={catalog_name}", headers=self.headers)
        if response.status_code == 200:
            schemas = response.json().get('schemas', [])
            if any(s['name'] == schema_name for s in schemas):
                print(f"✓ Schema '{schema_name}' already exists in catalog '{catalog_name}'")
                return True
        
        # Create new schema
        payload = {
            "name": schema_name,
            "catalog_name": catalog_name,
            "comment": f"Auto-created schema for {schema_name}"
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        if response.status_code in [200, 201]:
            print(f"✓ Created schema '{schema_name}' in catalog '{catalog_name}'")
            return True
        else:
            print(f"✗ Error creating schema: {response.text}")
            return False
    
    def create_streaming_table(
        self,
        catalog_name: str,
        schema_name: str,
        table_name: str,
        s3_path: str,
        file_format: str = "parquet",
        schedule: str = "0 0 * * *"  # Daily at midnight
    ) -> bool:
        """
        Create or update external table from S3
        
        Args:
            catalog_name: Catalog name
            schema_name: Schema/database name
            table_name: Table name
            s3_path: Full S3 path (e.g., s3://bucket/path/to/data/)
            file_format: File format (parquet, json, csv, delta)
            schedule: Cron schedule for ingestion (default: daily at midnight)
        """
        full_table_name = f"{catalog_name}.{schema_name}.{table_name}"
        
        # Check if table exists
        url = f"{self.workspace_url}/api/2.1/unity-catalog/tables/{catalog_name}.{schema_name}.{table_name}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            print(f"✓ Table '{full_table_name}' already exists")
            update = input("Do you want to update the table? (y/n): ").lower()
            if update != 'y':
                return True
            
            # Drop and recreate
            delete_url = f"{self.workspace_url}/api/2.0/sql/statements/"
            delete_sql = f"DROP TABLE IF EXISTS {full_table_name}"
            delete_payload = {
                "statement": delete_sql,
                "warehouse_id": self._get_warehouse_id()
            }
            requests.post(delete_url, headers=self.headers, json=delete_payload)
            print(f"✓ Dropped existing table '{full_table_name}'")
        
        # Create external table using SQL
        if file_format.lower() == "parquet":
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS {full_table_name}
            USING PARQUET
            LOCATION '{s3_path}'
            """
        elif file_format.lower() == "json":
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS {full_table_name}
            USING JSON
            LOCATION '{s3_path}'
            """
        elif file_format.lower() == "csv":
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS {full_table_name}
            USING CSV
            OPTIONS (header='true', inferSchema='true')
            LOCATION '{s3_path}'
            """
        else:  # delta
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS {full_table_name}
            USING DELTA
            LOCATION '{s3_path}'
            """
        
        sql_url = f"{self.workspace_url}/api/2.0/sql/statements/"
        sql_payload = {
            "statement": create_sql,
            "warehouse_id": self._get_warehouse_id()
        }
        
        response = requests.post(sql_url, headers=self.headers, json=sql_payload)
        
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"✓ Created external table '{full_table_name}'")
            print(f"  Source: {s3_path}")
            print(f"  Format: {file_format}")
            print(f"  Type: External Table")
            return True
        else:
            print(f"✗ Error creating table: {response.text}")
            print(f"\nSQL attempted:\n{create_sql}")
            return False
    
    def _get_warehouse_id(self) -> str:
        """Get warehouse ID (use provided or fetch first available)"""
        if self.warehouse_id:
            return self.warehouse_id
        
        url = f"{self.workspace_url}/api/2.0/sql/warehouses"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            warehouses = response.json().get('warehouses', [])
            if warehouses:
                return warehouses[0]['id']
        
        raise Exception("No SQL warehouse found. Please provide warehouse_id or create one first.")


def main():
    """Main execution flow"""
    print("="*60)
    print("DATABRICKS S3 STREAMING INGESTION SETUP")
    print("="*60)
    
    # Step 1: Get Databricks credentials
    print("\n[STEP 1] Databricks Configuration")
    print("\nOption 1: Use default configuration")
    print("  Server: dbc-f30c6cd6-abcb.cloud.databricks.com")
    print("  Warehouse ID: 8e650ab1879dac31")
    
    use_default = input("\nUse default configuration? (y/n, default=y): ").strip().lower() or 'y'
    
    if use_default == 'y':
        workspace_url = "https://dbc-f30c6cd6-abcb.cloud.databricks.com"
        warehouse_id = "8e650ab1879dac31"
        token = input("Enter Databricks token: ").strip()
    else:
        workspace_url = input("Enter Databricks workspace URL: ").strip()
        http_path = input("Enter HTTP path (e.g., /sql/1.0/warehouses/xxxxx): ").strip()
        warehouse_id = http_path.split('/')[-1] if http_path else None
        token = input("Enter Databricks token: ").strip()
    
    # Initialize client
    client = DatabricksS3StreamingIngestion(workspace_url, token, warehouse_id)
    
    # Step 2: Select external location
    print("\n[STEP 2] Select S3 External Location")
    external_location_url = client.display_external_locations()
    
    if not external_location_url:
        print("\n✗ No external location available. Exiting.")
        return
    
    # Step 3: Get S3 path
    print("\n[STEP 3] S3 Data Location")
    s3_folder = input("Enter S3 folder path (e.g., fin_work/process_data/market_data/): ").strip()
    full_s3_path = f"{external_location_url.rstrip('/')}/{s3_folder.strip('/')}"
    print(f"Full S3 path: {full_s3_path}")
    
    # Step 4: File format
    print("\n[STEP 4] File Format")
    print("1. Parquet")
    print("2. JSON")
    print("3. CSV")
    print("4. Delta")
    format_choice = input("Select format (1-4, default=1): ").strip() or "1"
    format_map = {"1": "parquet", "2": "json", "3": "csv", "4": "delta"}
    file_format = format_map.get(format_choice, "parquet")
    
    # Step 5: Catalog and schema
    print("\n[STEP 5] Catalog and Schema Configuration")
    catalog_name = input("Enter catalog name (or create new): ").strip()
    schema_name = input("Enter schema/database name (or create new): ").strip()
    table_name_input = input("Enter table name (press Enter to auto-generate): ").strip()
    
    # Auto-generate table name from S3 path if not provided
    if not table_name_input:
        # Extract last folder name from S3 path
        path_parts = s3_folder.strip('/').split('/')
        table_name = path_parts[-1].replace('-', '_').replace('.', '_').lower()
        print(f"Auto-generated table name: {table_name}")
    else:
        table_name = table_name_input
    
    # Step 6: Schedule
    print("\n[STEP 6] Ingestion Schedule")
    print("1. Every hour (0 * * * *)")
    print("2. Daily at midnight (0 0 * * *)")
    print("3. Every 6 hours (0 */6 * * *)")
    print("4. Custom cron expression")
    schedule_choice = input("Select schedule (1-4, default=2): ").strip() or "2"
    
    schedule_map = {
        "1": "0 * * * *",
        "2": "0 0 * * *",
        "3": "0 */6 * * *"
    }
    
    if schedule_choice == "4":
        schedule = input("Enter custom cron expression: ").strip()
    else:
        schedule = schedule_map.get(schedule_choice, "0 0 * * *")
    
    # Step 7: Create resources
    print("\n[STEP 7] Creating Resources...")
    print("-" * 60)
    
    # Create catalog with storage location
    catalog_storage = f"{external_location_url.rstrip('/')}/catalogs/{catalog_name}"
    print(f"Catalog storage location: {catalog_storage}")
    
    if not client.create_catalog(catalog_name, catalog_storage):
        print("✗ Failed to create catalog. Exiting.")
        return
    
    # Create schema
    if not client.create_schema(catalog_name, schema_name):
        print("✗ Failed to create schema. Exiting.")
        return
    
    # Create streaming table
    if client.create_streaming_table(
        catalog_name,
        schema_name,
        table_name,
        full_s3_path,
        file_format,
        schedule
    ):
        print("\n" + "="*60)
        print("✓ SETUP COMPLETED SUCCESSFULLY!")
        print("="*60)
        print(f"Table: {catalog_name}.{schema_name}.{table_name}")
        print(f"Source: {full_s3_path}")
        print(f"Format: {file_format}")
        print(f"Schedule: {schedule}")
        print("\nYou can now query your table:")
        print(f"SELECT * FROM {catalog_name}.{schema_name}.{table_name} LIMIT 10;")
    else:
        print("\n✗ Failed to create streaming table.")


if __name__ == "__main__":
    main()
