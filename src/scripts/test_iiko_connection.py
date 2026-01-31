
import asyncio
import os
import sys
import dotenv
from pathlib import Path

# Add src to python path to import services
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.services.iiko.client import IikoClient

# Load env from root
dotenv.load_dotenv(Path(__file__).parent.parent.parent / ".env")

async def main():
    print("--- Testing iiko connection ---")
    client = IikoClient()
    
    try:
        print(f"Authenticating with API Key: {client.api_key[:5]}...{client.api_key[-5:]}")
        token = await client.auth()
        print(f"Success! Token received: {token[:10]}...")
        
        print("Fetching organizations...")
        orgs = await client.get_organizations()
        print(f"Found {len(orgs)} organizations:")
        for org in orgs:
            print(f"- Name: {org.get('name')}, ID: {org.get('id')}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
