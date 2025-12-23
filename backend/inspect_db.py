import boto3
import os
import json
from decimal import Decimal

def decimal_to_python(obj):
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    if isinstance(obj, dict):
        return {k: decimal_to_python(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [decimal_to_python(i) for i in obj]
    return obj

def inspect():
    try:
        # Check if running inside docker or local
        endpoint = os.getenv("DYNAMODB_ENDPOINT", "http://localhost:8000")
        if "db:8000" in endpoint:
            # If we are running locally but the env says db:8000 (docker alias),
            # we need to use localhost:8000
            endpoint = "http://localhost:8000"
            
        dynamodb = boto3.resource(
            'dynamodb',
            endpoint_url=endpoint,
            region_name='us-east-1',
            aws_access_key_id='local',
            aws_secret_access_key='local'
        )
        
        # List all tables
        print(f"\n--- Checking DynamoDB at {endpoint} ---")
        client = boto3.client(
            'dynamodb', 
            endpoint_url=endpoint, 
            region_name='us-east-1',
            aws_access_key_id='local',
            aws_secret_access_key='local'
        )
        tables = client.list_tables()['TableNames']
        
        if not tables:
            print("No tables found.")
            return

        for table_name in tables:
            print(f"\n[Table: {table_name}]")
            table = dynamodb.Table(table_name)
            response = table.scan()
            items = response.get('Items', [])
            
            if not items:
                print("  (Empty)")
                continue
                
            for item in items:
                # Convert Decimals for pretty printing
                clean_item = decimal_to_python(item)
                print(json.dumps(clean_item, indent=2))
                
    except Exception as e:
        print(f"Error inspecting database: {e}")
        print("\nTip: Make sure your docker containers are running (`docker-compose up`)!")

if __name__ == "__main__":
    inspect()
