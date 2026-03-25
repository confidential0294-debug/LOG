import httpx
import asyncio

async def check():
    url = "http://localhost:10000/mcp"
    print(f"Testing {url}")
    async with httpx.AsyncClient() as client:
        try:
            # Test health
            resp = await client.get("http://localhost:10000/health")
            print(f"Health: {resp.status_code}")

            # Test MCP
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1.0"}
                }
            }
            resp = await client.post(url, json=payload, headers={"Accept": "application/json"})
            print(f"MCP Status: {resp.status_code}")
            print(f"MCP Body: {resp.text[:100]}...")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check())
