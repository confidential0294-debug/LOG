#!/usr/bin/env python3
"""
Minimal MCP Server for ChatGPT - Jupyter Notebook Controller
Exposes tools via SSE (Server-Sent Events) for ChatGPT remote MCP integration
"""

import os
import json
import subprocess
from pathlib import Path
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

# Configuration
WORKSPACE_ROOT = Path("/workspaces/LOG")
PORT = int(os.getenv("PORT", "8000"))
RENDER_SERVICE_NAME = os.getenv("RENDER_SERVICE_NAME")  # e.g. your-service-name

# Initialize FastMCP Server
mcp = FastMCP("jupyter-notebook-controller")

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

    notebooks = sorted(search_path.glob("**/*.ipynb"))
    notebook_list = [str(nb.relative_to(WORKSPACE_ROOT)) for nb in notebooks]

    text = f"Found {len(notebook_list)} notebooks:\n" +            "\n".join(f"  - {nb}" for nb in notebook_list) if notebook_list else "No notebooks found"

    return text

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

@mcp.tool()
async def get_mcp_url() -> str:
    """Get the public MCP server URL for ChatGPT configuration."""
    # Return the best known URL for this environment.
    if RENDER_SERVICE_NAME:
        url = f"https://{RENDER_SERVICE_NAME}.onrender.com/sse"
    else:
        codespace = os.getenv("CODESPACE_NAME")
        if codespace:
            url = f"https://{codespace}-8000.app.github.dev/sse"
        else:
            url = f"http://localhost:{PORT}/sse"

    text = f"MCP Server URL:\n{url}\n\nFor ChatGPT, configure it as:\n- Type: HTTP\n- URL: {url}"
    return text

# ============================================================================
# FastAPI App setup
# ============================================================================

app = FastAPI(title="Jupyter Notebook MCP Server")

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "service": "jupyter-notebook-mcp"}

# Mount FastMCP SSE app
app.mount("/", mcp.sse_app())

if __name__ == "__main__":
    import uvicorn
    host = "0.0.0.0"
    port = PORT

    if RENDER_SERVICE_NAME:
        public_url = f"https://{RENDER_SERVICE_NAME}.onrender.com/sse"
    else:
        codespace = os.getenv("CODESPACE_NAME")
        if codespace:
            public_url = f"https://{codespace}-{port}.app.github.dev/sse"
        else:
            public_url = f"http://localhost:{port}/sse"

    print(f"Starting Jupyter Notebook MCP Server on http://{host}:{port}")
    print(f"SSE endpoint: http://{host}:{port}/sse")
    print(f"Public URL: {public_url}")
    uvicorn.run(app, host=host, port=port, log_level="info")
