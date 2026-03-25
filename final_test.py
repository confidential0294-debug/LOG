import httpx
import asyncio
import os
import subprocess
import time

async def test():
    print("Starting local server for verification...")
    # Using 10000 to match Render config
    proc = subprocess.Popen(["uvicorn", "mcp_server:app", "--host", "0.0.0.0", "--port", "10000"])
    time.sleep(5)

    try:
        async with httpx.AsyncClient() as client:
            # 1. Test Root (Handshake)
            print("Checking /...")
            resp = await client.get("http://localhost:10000/")
            print(f"Status: {resp.status_code}, Text: {resp.text}")
            assert resp.status_code == 200

            # 2. Test SSE
            print("Checking /sse...")
            async with client.stream("GET", "http://localhost:10000/sse") as response:
                print(f"SSE Status: {response.status_code}")
                assert response.status_code == 200
                assert "text/event-stream" in response.headers["content-type"]

                # Check for endpoint message
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        print(f"Handshake data: {line[6:]}")
                        break
        print("\nLOCAL VERIFICATION SUCCESSFUL")
    finally:
        proc.kill()

if __name__ == "__main__":
    asyncio.run(test())
