"""Cross-Databricks Sharing - View Creation Only
Creates filtered views for sharing (manual share setup in UI)
"""

import requests
import sys
from typing import Dict, List

def masked_input(prompt: str) -> str:
    """Show asterisks while typing"""
    print(prompt, end='', flush=True)
    password = []
    
    if sys.platform == 'win32':
        import msvcrt
        while True:
            char = msvcrt.getch()
            if char in (b'\r', b'\n'):
                print()
                break
            elif char == b'\x08':
                if password:
                    password.pop()
                    print('\b \b', end='', flush=True)
            else:
                password.append(char.decode('utf-8'))
                print('*', end='', flush=True)
    else:
        import tty, termios
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while True:
                char = sys.stdin.read(1)
                if char in ('\r', '\n'):
                    print()
                    break
                elif char == '\x7f':
                    if password:
                        password.pop()
                        print('\b \b', end='', flush=True)
                else:
                    password.append(char)
                    print('*', end='', flush=True)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
    
    return ''.join(password)

class DatabricksViewCreator:
    def __init__(self, workspace_url: str, token: str, warehouse_id: str):
        self.workspace_url = workspace_url.rstrip('/')
        self.token = token
        self.warehouse_id = warehouse_id
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        self.created_views = []
    
    def execute_sql(self, sql: str) -> Dict:
        """Execute SQL statement"""
        url = f"{self.workspace_url}/api/2.0/sql/statements/"
        payload = {"statement": sql, "warehouse_id": self.warehouse_id}
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json() if response.status_code in [200, 201] else {}
    
    def list_catalogs(self) -> List[str]:
        """List all catalogs"""
        url = f"{self.workspace_url}/api/2.1/unity-catalog/catalogs"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return [c['name'] for c in response.json().get('catalogs', [])]
        return []
    
    def list_schemas(self, catalog: str) -> List[str]:
        """List schemas in catalog"""
        url = f"{self.workspace_url}/api/2.1/unity-catalog/schemas?catalog_name={catalog}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return [s['name'] for s in response.json().get('schemas', [])]
        return []
    
    def list_tables(self, catalog: str, schema: str) -> List[str]:
        """List tables in schema"""
        url = f"{self.workspace_url}/api/2.1/unity-catalog/tables?catalog_name={catalog}&schema_name={schema}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return [t['name'] for t in response.json().get('tables', [])]
        return []
    
    def list_views(self, catalog: str, schema: str) -> List[str]:
        """List views in schema"""
        url = f"{self.workspace_url}/api/2.1/unity-catalog/tables?catalog_name={catalog}&schema_name={schema}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return [t['name'] for t in response.json().get('tables', []) if t.get('table_type') == 'VIEW']
        return []
    
    def get_table_columns(self, table: str) -> List[str]:
        """Get list of columns from table"""
        sql = f"DESCRIBE TABLE {table}"
        result = self.execute_sql(sql)
        
        columns = []
        if result and 'result' in result:
            data = result.get('result', {}).get('data_array', [])
            for row in data:
                if len(row) >= 1:
                    columns.append(row[0])
        return columns
    
    def create_filtered_view(self, catalog: str, schema: str, base_table: str, 
                            view_name: str, columns: List[str] = None, 
                            row_filter: str = None) -> bool:
        """Create table with column and row filtering"""
        col_list = ", ".join(columns) if columns else "*"
        where_clause = f" WHERE {row_filter}" if row_filter else ""
        
        sql = f"""
        CREATE OR REPLACE TABLE {catalog}.{schema}.{view_name} AS
        SELECT {col_list}
        FROM {catalog}.{schema}.{base_table}{where_clause}
        """
        
        result = self.execute_sql(sql)
        if result:
            full_view_name = f"{catalog}.{schema}.{view_name}"
            self.created_views.append(full_view_name)
            print(f"✓ Table '{view_name}' created")
            if columns:
                print(f"  Columns: {', '.join(columns)}")
            if row_filter:
                print(f"  Row filter: {row_filter}")
            return True
        return False
    
    def create_share(self, share_name: str, views: List[str]) -> bool:
        """Attempt to create share via API"""
        url = f"{self.workspace_url}/api/2.1/unity-catalog/shares"
        payload = {"name": share_name}
        response = requests.post(url, headers=self.headers, json=payload)
        
        if response.status_code not in [200, 201]:
            return False
        
        for view in views:
            url = f"{self.workspace_url}/api/2.1/unity-catalog/shares/{share_name}/assets"
            payload = {"name": view, "asset_type": "TABLE"}
            response = requests.post(url, headers=self.headers, json=payload)
            if response.status_code not in [200, 201]:
                return False
        
        return True
    
    def list_shares(self) -> List[str]:
        """List existing shares"""
        url = f"{self.workspace_url}/api/2.1/unity-catalog/shares"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return [s['name'] for s in response.json().get('shares', [])]
        return []
    
    def add_to_share(self, share_name: str, views: List[str]) -> tuple[bool, str]:
        """Add views to existing share"""
        for view in views:
            url = f"{self.workspace_url}/api/2.1/unity-catalog/shares/{share_name}/assets"
            payload = {"name": view, "asset_type": "TABLE"}
            response = requests.post(url, headers=self.headers, json=payload)
            if response.status_code not in [200, 201]:
                error = response.json().get('message', response.text) if response.text else f"HTTP {response.status_code}"
                return False, error
        return True, ""

def main():
    print("="*60)
    print("DATABRICKS DELTA SHARING - TABLE CREATOR")
    print("="*60)
    
    print("\n[CONFIGURATION]")
    default_url = "https://dbc-f30c6cd6-abcb.cloud.databricks.com"
    default_warehouse = "8e650ab1879dac31"
    
    provider_url = input(f"Workspace URL [{default_url}]: ").strip()
    if not provider_url:
        provider_url = default_url
    
    warehouse_id = input(f"Warehouse ID [{default_warehouse}]: ").strip()
    if not warehouse_id:
        warehouse_id = default_warehouse
    
    provider_token = masked_input("Token: ").strip()
    print(f"✓ Token entered ({len(provider_token)} characters)")
    
    client = DatabricksViewCreator(provider_url, provider_token, warehouse_id)
    
    print("\n[CREATE FILTERED TABLES]")
    while True:
        print("\n" + "-"*60)
        
        print("Fetching catalogs...")
        catalogs = client.list_catalogs()
        
        if catalogs:
            print("\nAvailable Catalogs:")
            for i, cat in enumerate(catalogs, 1):
                print(f"{i}. {cat}")
            
            cat_choice = input("\nSelect catalog (or 'done'): ").strip()
            if cat_choice.lower() == 'done':
                break
            
            try:
                catalog = catalogs[int(cat_choice)-1]
            except:
                print("✗ Invalid selection")
                continue
            
            print(f"\nFetching schemas in {catalog}...")
            schemas = client.list_schemas(catalog)
            
            if schemas:
                print("\nAvailable Schemas:")
                for i, sch in enumerate(schemas, 1):
                    print(f"{i}. {sch}")
                
                sch_choice = input("\nSelect schema: ").strip()
                try:
                    schema = schemas[int(sch_choice)-1]
                except:
                    print("✗ Invalid selection")
                    continue
                
                print(f"\nFetching tables in {catalog}.{schema}...")
                tables = client.list_tables(catalog, schema)
                
                if tables:
                    print("\nAvailable Tables:")
                    for i, tbl in enumerate(tables, 1):
                        print(f"{i}. {tbl}")
                    
                    tbl_choice = input("\nSelect table: ").strip()
                    try:
                        base_table = tables[int(tbl_choice)-1]
                        table = f"{catalog}.{schema}.{base_table}"
                    except:
                        print("✗ Invalid selection")
                        continue
                else:
                    print("No tables found")
                    continue
            else:
                print("No schemas found")
                continue
        else:
            print("No catalogs found")
            break
        
        print("\nFilter Options:")
        print("1. Full table (no filtering)")
        print("2. Column filtering only")
        print("3. Row filtering only")
        print("4. Column + Row filtering")
        
        choice = input("\nChoice (1-4): ").strip()
        
        print("\nFetching existing tables...")
        existing_tables = client.list_tables(catalog, schema)
        
        table_name = None
        use_existing = False
        if existing_tables:
            print("\nExisting Tables:")
            for i, t in enumerate(existing_tables, 1):
                print(f"{i}. {t}")
            print(f"{len(existing_tables)+1}. Create new table")
            
            table_choice = input("\nSelect table or create new: ").strip()
            try:
                idx = int(table_choice) - 1
                if 0 <= idx < len(existing_tables):
                    table_name = existing_tables[idx]
                    use_existing = True
                    full_table_name = f"{catalog}.{schema}.{table_name}"
                    client.created_views.append(full_table_name)
                    print(f"✓ Using existing table: {table_name}")
            except:
                pass
        
        if use_existing:
            continue
        
        if not table_name:
            table_name = input("Table name for filtered data: ").strip()
        
        selected_columns = None
        row_filter = None
        
        if choice in ["2", "4"]:
            print("\nFetching columns...")
            columns = client.get_table_columns(table)
            if columns:
                print("\nAvailable columns:")
                for i, col in enumerate(columns, 1):
                    print(f"{i}. {col}")
                
                col_input = input("\nSelect columns (comma-separated numbers or 'all'): ").strip()
                if col_input.lower() != 'all':
                    indices = [int(x.strip())-1 for x in col_input.split(',')]
                    selected_columns = [columns[i] for i in indices if 0 <= i < len(columns)]
        
        if choice in ["3", "4"]:
            print("\nRow Filter Examples:")
            print("  - year >= 2023")
            print("  - status = 'active' AND date >= '2024-01-01'")
            print("  - amount > 1000")
            row_filter = input("\nEnter row filter: ").strip()
        
        client.create_filtered_view(
            catalog, schema, base_table, table_name,
            selected_columns, row_filter
        )
    
    print("\n" + "="*60)
    print("✓ TABLES CREATED SUCCESSFULLY!")
    print("="*60)
    
    if client.created_views:
        print("\nCreated Tables:")
        for view in client.created_views:
            print(f"  - {view}")
        
        share_choice = input("\nCreate share now? (y/n): ").strip().lower()
        if share_choice == 'y':
            print("\nFetching existing shares...")
            existing_shares = client.list_shares()
            
            share_name = None
            if existing_shares:
                print("\nExisting Shares:")
                for i, s in enumerate(existing_shares, 1):
                    print(f"{i}. {s}")
                print(f"{len(existing_shares)+1}. Create new share")
                
                share_sel = input("\nSelect share or create new: ").strip()
                try:
                    idx = int(share_sel) - 1
                    if 0 <= idx < len(existing_shares):
                        share_name = existing_shares[idx]
                        print(f"\nAdding views to existing share '{share_name}'...")
                        success, error = client.add_to_share(share_name, client.created_views)
                        if success:
                            print(f"✓ Views added to share '{share_name}'")
                            return
                        else:
                            print(f"✗ API Error: {error}")
                            print("\n" + "="*60)
                            print("MANUAL STEPS (Databricks UI)")
                            print("="*60)
                            print(f"\n1. Go to Data Explorer > Delta Sharing > '{share_name}'")
                            print("2. Click 'Add assets'")
                            print("3. Select these tables:")
                            for view in client.created_views:
                                print(f"   - {view}")
                            print("4. Save changes")
                            return
                except:
                    pass
            
            if not share_name:
                share_name = input("\nShare name: ").strip()
            
            print(f"\nCreating share '{share_name}'...")
            
            if client.create_share(share_name, client.created_views):
                print(f"✓ Share '{share_name}' created with views")
                print("\nNext: Create recipient and grant access via Databricks UI")
            else:
                print("✗ API share creation failed (workspace restrictions)")
                print("\n" + "="*60)
                print("MANUAL SHARING STEPS (Databricks UI)")
                print("="*60)
                print("\n1. Go to Databricks UI > Data Explorer")
                print("2. Click 'Delta Sharing' > 'Shared by me'")
                print("3. Click 'Create Share'")
                print(f"4. Enter share name: {share_name}")
                print("5. Add these tables:")
                for view in client.created_views:
                    print(f"   - {view}")
                print("6. Create Recipient:")
                print("")
                print("   CRITICAL: Both 'Databricks' and 'Open' recipient types")
                print("   require External Delta Sharing to be enabled.")
                print("")
                print("   YOU MUST contact Databricks Support:")
                print("   - Email: support@databricks.com")
                print("   - Subject: Enable External Delta Sharing on Metastore")
                print("   - Message: 'I need External Delta Sharing enabled on my")
                print("     metastore for cross-account data sharing'")
                print("   - Provide: Account email (tanmaymondal1320@gmail.com)")
                print("   - Provide: Workspace URL")
                print("   - Usually requires Premium/Enterprise tier")
                print("")
                print("   After enabled, create recipient (Databricks or Open type)")
                print("7. Grant SELECT permission to recipient")
                print("8. Copy and share activation URL with recipient")
                print("\nRecipient Setup:")
                print("1. Recipient receives activation URL")
                print("2. Go to Catalog > Delta Sharing > Shared with me")
                print("3. Click 'Create catalog from share'")
                print("4. Paste activation URL and create catalog")

if __name__ == "__main__":
    main()
