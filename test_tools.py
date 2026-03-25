import asyncio
from mcp_server import list_notebooks, read_notebook, run_shell_command

async def test():
    print("Testing list_notebooks...")
    res = await list_notebooks()
    print(res)
    assert "test_notebook.ipynb" in res

    print("\nTesting read_notebook...")
    res = await read_notebook("test_notebook.ipynb")
    print(res[:200] + "...")
    assert "Notebook: test_notebook.ipynb" in res

    print("\nTesting run_shell_command...")
    res = await run_shell_command("echo hello")
    print(res)
    assert "Exit code: 0" in res
    assert "hello" in res

    print("\nAll tools verified!")

if __name__ == "__main__":
    asyncio.run(test())
