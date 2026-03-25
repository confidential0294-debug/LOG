import urllib.request
import time

url = "https://mcp-server-log-actual-final-2.onrender.com/sse"
print(f"Testing SSE endpoint: {url}")

try:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as response:
        print(f"Status: {response.status}")
        print(f"Headers: {dict(response.headers)}")

        # Read first few bytes to check for event stream
        chunk = response.read(100)
        print(f"First chunk: {chunk}")

        if response.status == 200 and 'text/event-stream' in response.headers.get('Content-Type', ''):
            print("SSE verification SUCCESSFUL")
        else:
            print("SSE verification FAILED (unexpected status or content type)")
except Exception as e:
    print(f"SSE verification FAILED with error: {e}")
