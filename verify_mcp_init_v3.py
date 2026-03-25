import httpx
import json
import asyncio
import os
import subprocess
import time

async def test_init():
    url = "http://localhost:8000/sse"
    print(f"Testing MCP initialization (SSE) at {url}...")

    async with httpx.AsyncClient() as client:
        # Step 1: SSE connection
        try:
            async with client.stream("GET", url, timeout=30.0) as response:
                print(f"SSE Status: {response.status_code}")
                if response.status_code != 200:
                    return False

                full_messages_url = None

                # Use a task to read messages from the stream
                async def read_stream():
                    nonlocal full_messages_url
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            try:
                                data = json.loads(data_str)
                                print(f"Received data: {json.dumps(data, indent=2)}")
                                if "result" in data and "tools" in data["result"]:
                                    print("Tool discovery SUCCESSFUL")
                                    return True
                            except json.JSONDecodeError:
                                # Might be the endpoint string
                                if not full_messages_url:
                                    print(f"Received endpoint: {data_str}")
                                    full_messages_url = f"http://localhost:8000{data_str}"
                    return False

                # Start the background reader
                reader_task = asyncio.create_task(read_stream())

                # Wait a bit for the endpoint
                for _ in range(50):
                    if full_messages_url:
                        break
                    await asyncio.sleep(0.1)

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

                # Wait for the reader task to find the tools
                return await reader_task

        except Exception as e:
            print(f"Error: {e}")
    return False

if __name__ == "__main__":
    # Start server
    process = subprocess.Popen(["python3", "mcp_server.py"])
    time.sleep(5)

    try:
        success = asyncio.run(test_init())
        if success:
            print("MCP Initialization and Tool Listing verified!")
        else:
            print("MCP Verification FAILED!")
    finally:
        process.kill()
