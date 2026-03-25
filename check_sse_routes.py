from mcp.server.fastmcp import FastMCP
mcp = FastMCP("test")
app = mcp.sse_app()
for route in app.routes:
    print(f"Path: {route.path}, Methods: {route.methods if hasattr(route, 'methods') else 'N/A'}")
