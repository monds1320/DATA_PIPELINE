"""
Databricks S3 External Location Manager
Creates and manages external locations for S3 buckets in Databricks Unity Catalog
"""

import requests
import json
from typing import Optional, Dict, List


class DatabricksS3ExternalLocationManager:
    """Manage S3 external locations in Databricks Unity Catalog"""
    
    def __init__(self, workspace_url: str, token: str):
        """
        Initialize Databricks client
        
        Args:
            workspace_url: Databricks workspace URL (e.g., https://dbc-xxxxx.cloud.databricks.com)
            token: Personal access token
        """
        self.workspace_url = workspace_url.rstrip('/')
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def create_storage_credential(self, 
                                  credential_name: str,
                                  aws_iam_role_arn: str = None,
                                  aws_access_key_id: str = None,
                                  aws_secret_access_key: str = None,
                                  aws_session_token: str = None,
                                  comment: str = None) -> bool:
        """
        Create storage credential for S3 access
        
        Args:
            credential_name: Name for the credential
            aws_iam_role_arn: IAM role ARN (recommended for production)
            aws_access_key_id: AWS access key
            aws_secret_access_key: AWS secret key
            aws_session_token: AWS session token (for SSO/temporary credentials)
            comment: Optional description
            
        Returns:
            bool: Success status
        """
        url = f"{self.workspace_url}/api/2.1/unity-catalog/storage-credentials"
        
        # Check if credential exists
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                credentials = response.json().get('storage_credentials', [])
                if any(cred['name'] == credential_name for cred in credentials):
                    print(f"✓ Storage credential '{credential_name}' already exists")
                    return True
        except Exception as e:
            print(f"Warning: Could not check existing credentials: {e}")
        
        # Prepare payload
        payload = {
            "name": credential_name,
            "comment": comment or f"Storage credential for {credential_name}"
        }
        
        # Use IAM role (recommended) or access keys
        if aws_iam_role_arn:
            payload["aws_iam_role"] = {
                "role_arn": aws_iam_role_arn
            }
        elif aws_access_key_id and aws_secret_access_key:
            # Note: Databricks Unity Catalog requires IAM role, not access keys directly
            print("Warning: Unity Catalog requires IAM role. Access keys not supported.")
            print("Please use IAM role authentication instead.")
            return False
        else:
            print("Error: Must provide IAM role ARN")
            return False
        
        # Create credential
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            if response.status_code in [200, 201]:
                print(f"✓ Storage credential '{credential_name}' created successfully")
                return True
            else:
                print(f"✗ Failed to create credential: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        except Exception as e:
            print(f"✗ Error creating credential: {e}")
            return False
    
    def create_external_location(self,
                                 location_name: str,
                                 s3_url: str,
                                 credential_name: str,
                                 comment: str = None,
                                 read_only: bool = False) -> bool:
        """
        Create external location pointing to S3 bucket
        
        Args:
            location_name: Name for the external location
            s3_url: S3 URL (e.g., s3://bucket-name/path/)
            credential_name: Storage credential to use
            comment: Optional description
            read_only: Whether location is read-only
            
        Returns:
            bool: Success status
        """
        url = f"{self.workspace_url}/api/2.1/unity-catalog/external-locations"
        
        # Ensure S3 URL ends with /
        if not s3_url.endswith('/'):
            s3_url += '/'
        
        # Check if location exists
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                locations = response.json().get('external_locations', [])
                
                # Check by name
                for loc in locations:
                    if loc['name'] == location_name:
                        print(f"✓ External location '{location_name}' already exists")
                        print(f"  URL: {loc['url']}")
                        return True
                    
                    # Check for overlapping URL
                    if s3_url.startswith(loc['url']) or loc['url'].startswith(s3_url):
                        print(f"✓ Found existing external location '{loc['name']}' with overlapping path")
                        print(f"  Existing URL: {loc['url']}")
                        print(f"  Requested URL: {s3_url}")
                        print(f"\nOptions:")
                        print(f"1. Use existing location '{loc['name']}'")
                        print(f"2. Delete existing and create fine-grained location")
                        print(f"3. Cancel")
                        choice = input("Select (1-3): ").strip()
                        
                        if choice == '1':
                            print(f"✓ Using existing external location '{loc['name']}'")
                            return True
                        elif choice == '2':
                            print(f"\n⚠ Warning: This will delete '{loc['name']}' and may affect existing tables.")
                            confirm = input("Confirm deletion? (yes/no): ").strip().lower()
                            if confirm == 'yes':
                                if self.delete_external_location(loc['name']):
                                    print("Proceeding to create new location...")
                                    break
                                else:
                                    return False
                            else:
                                print("Cancelled.")
                                return False
                        else:
                            print("Cancelled.")
                            return False
        except Exception as e:
            print(f"Warning: Could not check existing locations: {e}")
        
        # Prepare payload
        payload = {
            "name": location_name,
            "url": s3_url,
            "credential_name": credential_name,
            "comment": comment or f"External location for {s3_url}",
            "read_only": read_only
        }
        
        # Create location
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            if response.status_code in [200, 201]:
                print(f"✓ External location '{location_name}' created successfully")
                print(f"  URL: {s3_url}")
                print(f"  Credential: {credential_name}")
                return True
            else:
                print(f"✗ Failed to create external location: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        except Exception as e:
            print(f"✗ Error creating external location: {e}")
            return False
    
    def list_storage_credentials(self) -> List[Dict]:
        """List all storage credentials"""
        url = f"{self.workspace_url}/api/2.1/unity-catalog/storage-credentials"
        
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                credentials = response.json().get('storage_credentials', [])
                print(f"\n{'='*60}")
                print(f"STORAGE CREDENTIALS ({len(credentials)} found)")
                print(f"{'='*60}")
                for cred in credentials:
                    print(f"\nName: {cred['name']}")
                    print(f"ID: {cred.get('id', 'N/A')}")
                    print(f"Created: {cred.get('created_at', 'N/A')}")
                return credentials
            else:
                print(f"Failed to list credentials: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error listing credentials: {e}")
            return []
    
    def list_external_locations(self) -> List[Dict]:
        """List all external locations"""
        url = f"{self.workspace_url}/api/2.1/unity-catalog/external-locations"
        
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                locations = response.json().get('external_locations', [])
                print(f"\n{'='*60}")
                print(f"EXTERNAL LOCATIONS ({len(locations)} found)")
                print(f"{'='*60}")
                for loc in locations:
                    print(f"\nName: {loc['name']}")
                    print(f"URL: {loc['url']}")
                    print(f"Credential: {loc['credential_name']}")
                    print(f"Read-only: {loc.get('read_only', False)}")
                return locations
            else:
                print(f"Failed to list locations: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error listing locations: {e}")
            return []
    
    def delete_external_location(self, location_name: str) -> bool:
        """Delete an external location"""
        url = f"{self.workspace_url}/api/2.1/unity-catalog/external-locations/{location_name}"
        
        try:
            response = requests.delete(url, headers=self.headers)
            if response.status_code in [200, 204]:
                print(f"✓ External location '{location_name}' deleted successfully")
                return True
            else:
                print(f"✗ Failed to delete location: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Error deleting location: {e}")
            return False


def main():
    """Interactive setup for S3 external locations"""
    
    print("="*60)
    print("DATABRICKS S3 EXTERNAL LOCATION SETUP")
    print("="*60)
    
    # Ask operation type
    print("\nSelect operation:")
    print("1. Create External Location")
    print("2. Delete External Location")
    operation = input("\nSelect (1-2): ").strip()
    
    # Configuration
    print("\n1. DATABRICKS CONFIGURATION")
    print("-" * 60)
    
    use_default = input("Use default configuration? (y/n): ").strip().lower()
    
    if use_default == 'y':
        workspace_url = "https://dbc-f30c6cd6-abcb.cloud.databricks.com"
        token = input("Enter Databricks token: ").strip()
    else:
        workspace_url = input("Enter workspace URL: ").strip()
        token = input("Enter Databricks token: ").strip()
    
    # Initialize client
    client = DatabricksS3ExternalLocationManager(workspace_url, token)
    
    # Execute based on operation
    if operation == '1':
        # Create flow
        print("\n2. CREATE STORAGE CREDENTIAL")
        print("-" * 60)
        credential_name = input("Credential name: ").strip()
        
        print("\nEnter IAM Role (name or full ARN):")
        print("Example: databricks-s3-ingest-c7a66-functionRole-FV2JXjQFGHEh")
        print("Or: arn:aws:iam::361769565206:role/databricks-s3-ingest-c7a66-functionRole-FV2JXjQFGHEh")
        iam_role_input = input("IAM Role: ").strip()
        
        # Convert to full ARN if only role name provided
        if iam_role_input.startswith('arn:aws:iam::'):
            iam_role = iam_role_input
        else:
            iam_role = f"arn:aws:iam::361769565206:role/{iam_role_input}"
        
        print(f"Using IAM Role ARN: {iam_role}")
        comment = input("Comment (optional): ").strip()
        
        client.create_storage_credential(
            credential_name=credential_name,
            aws_iam_role_arn=iam_role,
            comment=comment or None
        )
        
        print("\n3. CREATE EXTERNAL LOCATION")
        print("-" * 60)
        
        # Retry loop for external location creation
        max_retries = 3
        for attempt in range(max_retries):
            location_name = input("Location name: ").strip()
            s3_url = input("S3 URL (e.g., s3://bucket/path/): ").strip()
            read_only = input("Read-only? (y/n): ").strip().lower() == 'y'
            comment = input("Comment (optional): ").strip()
            
            success = client.create_external_location(
                location_name=location_name,
                s3_url=s3_url,
                credential_name=credential_name,
                comment=comment or None,
                read_only=read_only
            )
            
            if success:
                break
            else:
                if attempt < max_retries - 1:
                    print("\n⚠ Please try a different location name or S3 path.")
                    retry = input("Try again? (y/n): ").strip().lower()
                    if retry != 'y':
                        break
                else:
                    print("\n✗ Maximum retry attempts reached.")
    
    elif operation == '2':
        # Delete flow
        client.list_external_locations()
        print("\nDELETE EXTERNAL LOCATION")
        print("-" * 60)
        location_name = input("Location name to delete: ").strip()
        confirm = input(f"Delete '{location_name}'? (yes/no): ").strip().lower()
        if confirm in ['yes', 'y']:
            client.delete_external_location(location_name)
        else:
            print("Deletion cancelled.")
    
    else:
        print("Invalid operation")



if __name__ == "__main__":
    main()
