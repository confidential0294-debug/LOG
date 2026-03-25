import httpx
import json
import asyncio
import os
import subprocess
import time

async def test_init():
    # Streamable HTTP usually mounts at the root / if not specified
    # Or we can check the default mount path
    url = "http://localhost:8000/"
    print(f"Testing MCP initialization (Streamable HTTP) at {url}...")

    async with httpx.AsyncClient() as client:
        # Step 1: Initialize request
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

        print(f"Sending initialize to {url}...")
        try:
            init_resp = await client.post(url, json=init_payload, timeout=10.0)
            print(f"Initialize POST status: {init_resp.status_code}")
            print(f"Initialize POST response: {json.dumps(init_resp.json(), indent=2)}")

            if init_resp.status_code != 200:
                return False

            # Step 2: Tool discovery
            tools_payload = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            print(f"Sending tools/list to {url}...")
            tools_resp = await client.post(url, json=tools_payload, timeout=10.0)
            print(f"Tools list status: {tools_resp.status_code}")
            data = tools_resp.json()
            print(f"Tools list response: {json.dumps(data, indent=2)}")

            if "result" in data and "tools" in data["result"]:
                print("Tool discovery SUCCESSFUL")
                return True
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
        process.terminate()
