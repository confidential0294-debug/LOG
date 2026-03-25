#!/usr/bin/env python3
"""
MCP Server for Jupyter Notebook Controller
Exposes tools via Streamable HTTP for robust remote MCP integration.
"""

import os
import json
import subprocess
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# Configuration
WORKSPACE_ROOT = Path("/workspaces/LOG")
PORT = int(os.getenv("PORT", "10000"))

# Initialize FastMCP Server
mcp = FastMCP("jupyter-notebook-controller", stateless_http=True, json_response=True)

# ============================================================================
# Tool Definitions
# ============================================================================

@mcp.tool()
async def list_notebooks(path: str = "") -> str:
    """List all Jupyter notebook files (.ipynb) in the workspace."""
    search_path = WORKSPACE_ROOT / path if path else WORKSPACE_ROOT
    try:
        notebooks = sorted(search_path.glob("**/*.ipynb"))
        notebook_list = [str(nb.relative_to(WORKSPACE_ROOT)) for nb in notebooks]
        return f"Found {len(notebook_list)} notebooks:\n" + "\n".join(f"  - {nb}" for nb in notebook_list)
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
async def read_notebook(notebook_path: str) -> str:
    """Read and display the contents of a Jupyter notebook."""
    nb_path = WORKSPACE_ROOT / notebook_path
    if not nb_path.exists(): return f"Error: Not found"
    try:
        with open(nb_path, 'r') as f:
            notebook = json.load(f)
        output = f"Notebook: {notebook_path}\n"
        for i, cell in enumerate(notebook.get("cells", []), 1):
            source = cell.get('source', [])
            output += f"\n[Cell {i}] " + (''.join(source) if isinstance(source, list) else source)[:500]
        return output
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
async def run_shell_command(command: str, cwd: str = None) -> str:
    """Execute a shell command in the workspace."""
    try:
        result = subprocess.run(command, shell=True, cwd=cwd or str(WORKSPACE_ROOT), capture_output=True, text=True, timeout=30)
        return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    except Exception as e:
        return f"Error: {e}"

# ============================================================================
# Web Server Setup
# ============================================================================

# We use the built-in app directly which handles lifespan and session manager
# correctly. We just need to make sure the uvicorn entry point is right.
app = mcp.streamable_http_app()

if __name__ == "__main__":
    import uvicorn
    # Locally we run on PORT 10000
    uvicorn.run(app, host="0.0.0.0", port=PORT)
