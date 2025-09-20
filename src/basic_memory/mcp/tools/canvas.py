"""Canvas creation tool for Basic Memory MCP server.

This tool creates Obsidian canvas files (.canvas) using the JSON Canvas 1.0 spec.
"""

import json
from typing import List, Optional, Dict, Any, TypedDict

from loguru import logger
from fastmcp import Context

from basic_memory.mcp.async_client import client
from basic_memory.mcp.project_context import get_active_project
from basic_memory.mcp.server import mcp
from basic_memory.mcp.tools.utils import call_put


class CanvasNode(TypedDict, total=False):
    """Canvas node following JSON Canvas 1.0 spec."""
    id: str
    type: str
    x: int
    y: int
    width: int
    height: int
    file: str
    text: str
    url: str
    color: str
    label: str


class CanvasEdge(TypedDict, total=False):
    """Canvas edge following JSON Canvas 1.0 spec."""
    id: str
    fromNode: str
    toNode: str
    fromSide: str
    toSide: str
    color: str
    label: str


@mcp.tool(
    description="Create an Obsidian canvas file to visualize concepts and connections.",
)
async def canvas(
    nodes: List[CanvasNode],
    edges: List[CanvasEdge],
    title: str,
    folder: str,
    project: Optional[str] = None,
    context: Context | None = None,
) -> str:
    """Create an Obsidian canvas file with the provided nodes and edges.

    This tool creates a .canvas file compatible with Obsidian's Canvas feature,
    allowing visualization of relationships between concepts or documents.

    For the full JSON Canvas 1.0 specification, see the 'spec://canvas' resource.

    Args:
        nodes: List of node objects following JSON Canvas 1.0 spec. Each node must have:
               - id (str): Unique identifier for the node
               - type (str): Node type - "file", "text", "link", or "group"
               - x (int): X coordinate position in pixels
               - y (int): Y coordinate position in pixels
               - width (int): Width in pixels
               - height (int): Height in pixels
               Optional fields:
               - file (str): Path to file for "file" type nodes
               - text (str): Text content for "text" type nodes
               - url (str): URL for "link" type nodes
               - color (str): Color code ("1"-"6" or hex)
               - label (str): Display label
        edges: List of edge objects following JSON Canvas 1.0 spec. Each edge must have:
               - id (str): Unique identifier for the edge
               - fromNode (str): ID of source node
               - toNode (str): ID of target node
               Optional fields:
               - fromSide (str): Side of source node ("top", "right", "bottom", "left")
               - toSide (str): Side of target node ("top", "right", "bottom", "left")
               - color (str): Color code ("1"-"6" or hex)
               - label (str): Edge label text
        title: The title of the canvas (will be saved as title.canvas)
        folder: Folder path relative to project root where the canvas should be saved.
                Use forward slashes (/) as separators. Examples: "diagrams", "projects/2025", "visual/maps"
        project: Optional project name to create canvas in. If not provided, uses current active project.
        context: Optional context to use for this tool.

    Returns:
        A summary of the created canvas file

    Important Notes:
    - When referencing files, use the exact file path as shown in Obsidian
      Example: "folder/Document Name.md" (not permalink format)
    - For file nodes, the "file" attribute must reference an existing file
    - Position nodes in a logical layout (x,y coordinates in pixels)
    - Use color attributes ("1"-"6" or hex) for visual organization

    Basic Structure:
    ```json
    {
      "nodes": [
        {
          "id": "node1",
          "type": "file",
          "file": "folder/Document.md",
          "x": 0,
          "y": 0,
          "width": 400,
          "height": 300,
          "color": "1",
          "label": "Main Document"
        }
      ],
      "edges": [
        {
          "id": "edge1",
          "fromNode": "node1",
          "toNode": "node2",
          "fromSide": "right",
          "toSide": "left",
          "color": "2",
          "label": "connects to"
        }
      ]
    }
    ```

    Examples:
        # Create canvas in current project
        canvas(nodes=[...], edges=[...], title="My Canvas", folder="diagrams")

        # Create canvas in specific project
        canvas(nodes=[...], edges=[...], title="My Canvas", folder="diagrams", project="work-project")
    """
    active_project = await get_active_project(client, context=context, project_override=project)
    project_url = active_project.project_url

    # Ensure path has .canvas extension
    file_title = title if title.endswith(".canvas") else f"{title}.canvas"
    file_path = f"{folder}/{file_title}"

    # Create canvas data structure
    canvas_data = {"nodes": nodes, "edges": edges}

    # Convert to JSON
    canvas_json = json.dumps(canvas_data, indent=2)

    # Write the file using the resource API
    logger.info(f"Creating canvas file: {file_path}")
    response = await call_put(client, f"{project_url}/resource/{file_path}", json=canvas_json)

    # Parse response
    result = response.json()
    logger.debug(result)

    # Build summary
    action = "Created" if response.status_code == 201 else "Updated"
    summary = [f"# {action}: {file_path}", "\nThe canvas is ready to open in Obsidian."]

    return "\n".join(summary)
