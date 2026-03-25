from mcp.server.fastmcp import FastMCP
mcp = FastMCP("test")
# Access private attribute to find the internal app
internal_app = mcp._mcp_server.streamable_http_app()
for route in internal_app.routes:
    print(f"Internal Path: {route.path}")
