"""Test MCP server connection"""
import httpx
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_connection():
    mcp_url = os.getenv("MCP_SERVER_URL", "http://localhost:8000")
    
    print(f"Testing connection to: {mcp_url}")
    
    async with httpx.AsyncClient() as client:
        try:
            # Test JSON-RPC format
            response = await client.post(
                mcp_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/list"
                },
                timeout=5.0
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            
            if response.status_code == 200:
                print("✅ MCP Server is running!")
            else:
                print("❌ MCP Server returned error")
                
        except httpx.ConnectError:
            print("❌ Cannot connect to MCP server!")
            print(f"   Make sure the server is running on {mcp_url}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_connection())
