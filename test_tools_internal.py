import asyncio
import json
from mcp_server import server

async def test():
    print("Listing tools...")
    tools = await server.list_tools()
    print(f"Tools found: {[t['name'] for t in tools]}")

    print("\nCalling list_notebooks...")
    res = await server.call_tool("list_notebooks", {})
    print(res['text'])

    print("\nCalling run_shell_command...")
    res = await server.call_tool("run_shell_command", {"command": "echo 'hello from test'"})
    print(res['text'])

    print("\nInternal tools verification SUCCESSFUL")

if __name__ == "__main__":
    asyncio.run(test())
