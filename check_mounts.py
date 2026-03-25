from starlette.routing import Mount, Route
def print_routes(app, indent=0):
    for route in app.routes:
        prefix = "  " * indent
        if isinstance(route, Mount):
            print(f"{prefix}Mount: {route.path}")
            print_routes(route.app, indent + 1)
        elif isinstance(route, Route):
            print(f"{prefix}Route: {route.path}")

from mcp.server.fastmcp import FastMCP
mcp = FastMCP("test")
app = mcp.streamable_http_app()
print_routes(app)
