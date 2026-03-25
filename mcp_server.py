#!/usr/bin/env python3
"""
MCP Server for Jupyter Notebook Controller
Exposes tools via Streamable HTTP for robust remote MCP integration
"""

import os
import json
import subprocess
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Mount

# Configuration
WORKSPACE_ROOT = Path("/workspaces/LOG")
PORT = int(os.getenv("PORT", "8000"))

# Initialize FastMCP Server with stateless HTTP support (standard for Streamable HTTP)
mcp = FastMCP("jupyter-notebook-controller", stateless_http=True, json_response=True)

# ============================================================================
# Tool Definitions and Handlers
# ============================================================================

@mcp.tool()
async def list_notebooks(path: str = "") -> str:
    """List all Jupyter notebook files (.ipynb) in the workspace.

    Args:
        path: Directory path to search (default: workspace root)
    """
    search_path = WORKSPACE_ROOT / path if path else WORKSPACE_ROOT

    try:
        notebooks = sorted(search_path.glob("**/*.ipynb"))
        notebook_list = [str(nb.relative_to(WORKSPACE_ROOT)) for nb in notebooks]

        text = f"Found {len(notebook_list)} notebooks:\n" +                "\n".join(f"  - {nb}" for nb in notebook_list) if notebook_list else "No notebooks found"

        return text
    except Exception as e:
        return f"Error listing notebooks: {e}"

@mcp.tool()
async def read_notebook(notebook_path: str) -> str:
    """Read and display the contents of a Jupyter notebook.
    
    Args:
        notebook_path: Path to the .ipynb file (relative to workspace root)
    """
    nb_path = WORKSPACE_ROOT / notebook_path

    if not nb_path.exists():
        return f"Error: Notebook not found at {nb_path}"

    try:
        with open(nb_path, 'r') as f:
            notebook = json.load(f)
        
        # Format notebook for readability
        output = f"Notebook: {notebook_path}\n"
        output += f"Cells: {len(notebook.get('cells', []))}\n"
        output += "-" * 60 + "\n"
        
        for i, cell in enumerate(notebook.get("cells", []), 1):
            output += f"\n[Cell {i}] Type: {cell.get('cell_type', 'unknown')}\n"
            source = cell.get('source', [])
            content = ''.join(source) if isinstance(source, list) else source
            output += content[:500]  # Limit output
            if len(content) > 500:
                output += "\n... (truncated)"
        
        return output
    except Exception as e:
        return f"Error reading notebook: {e}"

@mcp.tool()
async def run_shell_command(command: str, cwd: str = None) -> str:
    """Execute a shell command in the workspace.

    Args:
        command: Shell command to execute
        cwd: Working directory (default: workspace root)
    """
    exec_cwd = cwd if cwd else str(WORKSPACE_ROOT)

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=exec_cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        output = f"Command: {command}\n"
        output += f"Exit code: {result.returncode}\n\n"
        output += "STDOUT:\n" + result.stdout if result.stdout else "STDOUT: (empty)"
        if result.stderr:
            output += "\n\nSTDERR:\n" + result.stderr
        return output
    except subprocess.TimeoutExpired:
        return "Error: Command timeout after 30 seconds"
    except Exception as e:
        return f"Error executing command: {e}"

# ============================================================================
# ASGI App for Render
# ============================================================================

# Use the built-in streamable_http_app() directly
# Note: Streamable HTTP in FastMCP handles sessions/requests at /mcp by default
app = mcp.streamable_http_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
