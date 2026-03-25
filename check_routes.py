from mcp.server.fastmcp import FastMCP
mcp = FastMCP("test")
app = mcp.streamable_http_app()
for route in app.routes:
    print(f"Path: {route.path}")
