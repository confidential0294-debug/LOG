from mcp_server import app
for route in app.routes:
    print(f"Path: {route.path}")
