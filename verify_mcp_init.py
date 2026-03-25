import httpx
import json
import asyncio

async def test_init():
    url = "http://localhost:8000/sse"
    print(f"Testing MCP initialization at {url}...")

    async with httpx.AsyncClient() as client:
        # Step 1: SSE connection
        async with client.stream("GET", url, timeout=30.0) as response:
            print(f"SSE Status: {response.status_code}")

            full_messages_url = None
            async for line in response.aiter_lines():
                if line.startswith("event: endpoint"):
                    continue
                if line.startswith("data: "):
                    endpoint_path = line[6:]
                    print(f"Received endpoint: {endpoint_path}")
                    full_messages_url = f"http://localhost:8000{endpoint_path}"
                    break

            if not full_messages_url:
                print("Failed to get messages endpoint from SSE")
                return False

            # Step 2: Initialize request
            init_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "0.1.0"}
                }
            }

            print(f"Sending initialize to {full_messages_url}...")
            init_resp = await client.post(full_messages_url, json=init_payload)
            print(f"Initialize POST status: {init_resp.status_code}")

            # Step 3: Tool discovery
            tools_payload = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            print(f"Sending tools/list to {full_messages_url}...")
            tools_resp = await client.post(full_messages_url, json=tools_payload)
            print(f"Tools list status: {tools_resp.status_code}")

            # Now read the stream for responses
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        print(f"Received data: {json.dumps(data, indent=2)}")
                        if "result" in data and "tools" in data["result"]:
                            print("Tool discovery SUCCESSFUL")
                            return True
                    except json.JSONDecodeError:
                        continue
    return False

if __name__ == "__main__":
    import os
    import subprocess
    import time

    # Start server
    process = subprocess.Popen(["uvicorn", "mcp_server:app", "--host", "0.0.0.0", "--port", "8000"])
    time.sleep(5)

    try:
        success = asyncio.run(test_init())
        if success:
            print("MCP Initialization and Tool Listing verified!")
        else:
            print("MCP Verification FAILED!")
    finally:
        process.kill() # Hard kill
