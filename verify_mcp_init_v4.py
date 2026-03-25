import httpx
import json
import asyncio
import os
import subprocess
import time

async def test_init():
    # Streamable HTTP mounts at / in FastMCP if used directly?
    # Let's try /mcp just in case it's hardcoded
    url = "http://localhost:8000/mcp"
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

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        try:
            init_resp = await client.post(url, json=init_payload, headers=headers, timeout=10.0)
            print(f"Initialize POST status: {init_resp.status_code}")
            if init_resp.status_code == 200:
                print("Initialize SUCCESSFUL")
                return True
        except Exception as e:
            print(f"Error: {e}")

    return False

if __name__ == "__main__":
    process = subprocess.Popen(["python3", "mcp_server.py"])
    time.sleep(5)
    try:
        if asyncio.run(test_init()):
            print("Verified!")
    finally:
        process.kill()
