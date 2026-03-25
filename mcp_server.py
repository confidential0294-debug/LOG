#!/usr/bin/env python3
"""
Definitive MCP Server for Jupyter Notebook Controller
Exposes tools via SSE transport for ChatGPT Remote MCP.
"""

import os
import json
import subprocess
import logging
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from starlette.routing import Route
from starlette.responses import Response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-server")

# Configuration
WORKSPACE_ROOT = Path.cwd()
PORT = int(os.getenv("PORT", "10000"))

# Initialize FastMCP
mcp = FastMCP("jupyter-notebook-controller")

# ============================================================================
# Tool Definitions
# ============================================================================

@mcp.tool()
async def list_notebooks(path: str = "") -> str:
    """List all Jupyter notebook files (.ipynb) in the workspace."""
    try:
        search_path = WORKSPACE_ROOT / path if path else WORKSPACE_ROOT
        notebooks = sorted(search_path.glob("**/*.ipynb"))
        notebook_list = [str(nb.relative_to(WORKSPACE_ROOT)) for nb in notebooks]
        return f"Found {len(notebook_list)} notebooks:\n" + "\n".join(f"  - {nb}" for nb in notebook_list)
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
async def read_notebook(notebook_path: str) -> str:
    """Read and display the contents of a Jupyter notebook."""
    try:
        nb_path = WORKSPACE_ROOT / notebook_path
        if not nb_path.exists(): return "Error: Not found"
        with open(nb_path, 'r') as f:
            notebook = json.load(f)
        output = f"Notebook: {notebook_path}\n"
        for i, cell in enumerate(notebook.get("cells", []), 1):
            source = cell.get('source', [])
            content = ''.join(source) if isinstance(source, list) else source
            output += f"\n[Cell {i}] {content[:200]}..."
        return output
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
async def run_shell_command(command: str, cwd: str = None) -> str:
    """Execute a shell command in the workspace."""
    try:
        result = subprocess.run(
            command, shell=True,
            cwd=cwd or str(WORKSPACE_ROOT),
            capture_output=True, text=True, timeout=30
        )
        return f"Exit code: {result.returncode}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    except Exception as e:
        return f"Error: {e}"

# ============================================================================
# Web Server Setup
# ============================================================================

# Create the standard SSE app
app = mcp.sse_app()

# Add a root route so ChatGPT and Users can verify the server is live
async def home(request):
    return Response(
        "Jupyter MCP Server is Running.\nConnect to /sse in ChatGPT.",
        media_type="text/plain"
    )

# Inject root route
app.routes.append(Route("/", home))

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting MCP server on port {PORT}...")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
