#!/usr/bin/env python3
"""
Minimal MCP Server for ChatGPT - Jupyter Notebook Controller
Exposes tools via SSE (Server-Sent Events) for ChatGPT remote MCP integration
"""

import os
import json
import subprocess
import asyncio
from pathlib import Path

from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse
from mcp.server import Server
from mcp.server.models import InitializationOptions
from contextlib import asynccontextmanager

# Configuration
WORKSPACE_ROOT = Path("/workspaces/LOG")
PORT = int(os.getenv("PORT", "8000"))
RENDER_SERVICE_NAME = os.getenv("RENDER_SERVICE_NAME")  # e.g. your-service-name

# Initialize MCP Server
server = Server("jupyter-notebook-controller")

# Initialize FastAPI app
app = FastAPI(title="Jupyter Notebook MCP Server")

# Global reference to keep track of server initialization
server_initialized = False


# ============================================================================
# Tool Definitions and Handlers
# ============================================================================

@server.list_tools()
async def list_tools():
    """List available tools for notebook control"""
    return [
        {
            "name": "list_notebooks",
            "description": "List all Jupyter notebook files (.ipynb) in the workspace",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory path to search (default: workspace root)"
                    }
                },
                "required": []
            }
        },
        {
            "name": "read_notebook",
            "description": "Read and display the contents of a Jupyter notebook",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "notebook_path": {
                        "type": "string",
                        "description": "Path to the .ipynb file (relative to workspace root)"
                    }
                },
                "required": ["notebook_path"]
            }
        },
        {
            "name": "run_shell_command",
            "description": "Execute a shell command in the workspace",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Shell command to execute"
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory (default: workspace root)"
                    }
                },
                "required": ["command"]
            }
        },
        {
            "name": "get_mcp_url",
            "description": "Get the public MCP server URL for ChatGPT configuration",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Execute tool requests"""
    
    if name == "list_notebooks":
        path = arguments.get("path", "")
        search_path = WORKSPACE_ROOT / path if path else WORKSPACE_ROOT
        
        notebooks = sorted(search_path.glob("**/*.ipynb"))
        notebook_list = [str(nb.relative_to(WORKSPACE_ROOT)) for nb in notebooks]
        
        text = f"Found {len(notebook_list)} notebooks:\n" + \
               "\n".join(f"  - {nb}" for nb in notebook_list) if notebook_list else "No notebooks found"
        
        return {"type": "text", "text": text}
    
    elif name == "read_notebook":
        nb_path = WORKSPACE_ROOT / arguments["notebook_path"]
        
        if not nb_path.exists():
            return {"type": "text", "text": f"Error: Notebook not found at {nb_path}"}
        
        try:
            with open(nb_path, 'r') as f:
                notebook = json.load(f)
            
            # Format notebook for readability
            output = f"Notebook: {arguments['notebook_path']}\n"
            output += f"Cells: {len(notebook.get('cells', []))}\n"
            output += "-" * 60 + "\n"
            
            for i, cell in enumerate(notebook.get("cells", []), 1):
                output += f"\n[Cell {i}] Type: {cell.get('cell_type', 'unknown')}\n"
                source = cell.get('source', [])
                content = ''.join(source) if isinstance(source, list) else source
                output += content[:500]  # Limit output
                if len(content) > 500:
                    output += "\n... (truncated)"
            
            return {"type": "text", "text": output}
        except Exception as e:
            return {"type": "text", "text": f"Error reading notebook: {e}"}
    
    elif name == "run_shell_command":
        command = arguments["command"]
        cwd = arguments.get("cwd", str(WORKSPACE_ROOT))
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=30
            )
            output = f"Command: {command}\n"
            output += f"Exit code: {result.returncode}\n\n"
            output += "STDOUT:\n" + result.stdout if result.stdout else "STDOUT: (empty)"
            if result.stderr:
                output += "\n\nSTDERR:\n" + result.stderr
            return {"type": "text", "text": output}
        except subprocess.TimeoutExpired:
            return {"type": "text", "text": "Error: Command timeout after 30 seconds"}
        except Exception as e:
            return {"type": "text", "text": f"Error executing command: {e}"}
    
    elif name == "get_mcp_url":
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
        return {"type": "text", "text": text}
    
    else:
        return {"type": "text", "text": f"Unknown tool: {name}"}


# ============================================================================
# FastAPI Routes with SSE Support
# ============================================================================

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "service": "jupyter-notebook-mcp"}


@app.get("/sse")
async def sse_endpoint():
    """SSE endpoint for ChatGPT MCP remote protocol"""
    from mcp.server.sse import SseServerTransport
    
    async def event_generator():
        transport = SseServerTransport("/sse/messages")
        async with transport:
            await server.run(transport)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


@app.post("/sse/messages")
async def sse_messages(request_body: dict):
    """Message handler for SSE protocol"""
    return {"status": "ok"}


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
