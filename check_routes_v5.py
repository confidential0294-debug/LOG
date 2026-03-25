from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import Response

mcp = FastMCP("test")
mcp_sse_app = mcp.sse_app()
app = Starlette(
    routes=[
        Route("/", lambda r: Response("ok")),
        Mount("/", app=mcp_sse_app),
    ]
)
for route in app.routes:
    if isinstance(route, Mount):
        print(f"Mount: {route.path}")
        for r in route.app.routes:
             print(f"  Route: {r.path}")
    else:
        print(f"Route: {route.path}")
