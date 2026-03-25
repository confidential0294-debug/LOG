import requests
import time
import subprocess
import os

# Start server in background
env = os.environ.copy()
env["PORT"] = "8000"
process = subprocess.Popen(["uvicorn", "mcp_server:app", "--host", "0.0.0.0", "--port", "8000"], env=env)
time.sleep(5)

try:
    print("Testing /health...")
    resp = requests.get("http://localhost:8000/health")
    print(f"Status: {resp.status_code}, Body: {resp.json()}")
    assert resp.status_code == 200

    print("\nTesting /sse GET...")
    # Stream for a bit to ensure it doesn't crash
    resp = requests.get("http://localhost:8000/sse", stream=True, timeout=5)
    print(f"Status: {resp.status_code}")
    print(f"Headers: {resp.headers}")
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers.get("Content-Type", "")

    print("\nEndpoints verification SUCCESSFUL")
finally:
    process.terminate()
