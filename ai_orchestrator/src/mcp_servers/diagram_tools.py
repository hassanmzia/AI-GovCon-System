"""MCP tool server: Architecture diagram generation via Mermaid, D2, and PlantUML."""
import base64
import logging
import os
from typing import Any, Literal

import httpx

logger = logging.getLogger("ai_orchestrator.mcp.diagrams")

DiagramFormat = Literal["mermaid", "d2", "plantuml"]
OutputFormat = Literal["svg", "png", "text"]

# Optional rendering service URLs (can be self-hosted or public)
_MERMAID_API = os.getenv("MERMAID_API_URL", "https://mermaid.ink")
_KROKI_API = os.getenv("KROKI_API_URL", "https://kroki.io")  # supports D2, PlantUML


async def generate_mermaid_diagram(
    diagram_definition: str,
    output_format: OutputFormat = "svg",
    theme: str = "default",
) -> dict[str, Any]:
    """Render a Mermaid diagram definition to SVG/PNG.

    Args:
        diagram_definition: Mermaid diagram source (e.g. ``graph LR\\n  A --> B``).
        output_format: "svg" or "png".
        theme: Mermaid theme ("default", "forest", "dark", "neutral").

    Returns:
        Dict with keys: diagram_source, output_format, image_data (base64), url.
    """
    try:
        encoded = base64.urlsafe_b64encode(diagram_definition.encode()).decode()
        fmt = "svg" if output_format == "svg" else "img"
        url = f"{_MERMAID_API}/{fmt}/{encoded}"

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            image_data = base64.b64encode(resp.content).decode()

        return {
            "diagram_source": diagram_definition,
            "format": "mermaid",
            "output_format": output_format,
            "image_data": image_data,
            "url": url,
            "content_type": "image/svg+xml" if output_format == "svg" else "image/png",
        }
    except Exception as exc:
        logger.warning("Mermaid render failed, returning source only: %s", exc)
        return {
            "diagram_source": diagram_definition,
            "format": "mermaid",
            "output_format": "text",
            "image_data": None,
            "url": None,
            "note": str(exc),
        }


async def generate_d2_diagram(
    diagram_definition: str,
    output_format: OutputFormat = "svg",
    layout: str = "dagre",
) -> dict[str, Any]:
    """Render a D2 diagram definition to SVG/PNG via Kroki.

    Args:
        diagram_definition: D2 diagram source code.
        output_format: "svg" or "png".
        layout: D2 layout engine ("dagre", "elk", "tala").

    Returns:
        Dict with keys: diagram_source, output_format, image_data (base64), url.
    """
    try:
        import zlib

        compressed = zlib.compress(diagram_definition.encode("utf-8"), 9)
        encoded = base64.urlsafe_b64encode(compressed).decode()
        url = f"{_KROKI_API}/d2/{output_format}/{encoded}"

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            image_data = base64.b64encode(resp.content).decode()

        return {
            "diagram_source": diagram_definition,
            "format": "d2",
            "output_format": output_format,
            "image_data": image_data,
            "url": url,
            "content_type": "image/svg+xml" if output_format == "svg" else "image/png",
        }
    except Exception as exc:
        logger.warning("D2 render failed, returning source only: %s", exc)
        return {
            "diagram_source": diagram_definition,
            "format": "d2",
            "output_format": "text",
            "image_data": None,
            "note": str(exc),
        }


async def generate_plantuml_diagram(
    diagram_definition: str,
    output_format: OutputFormat = "svg",
) -> dict[str, Any]:
    """Render a PlantUML diagram to SVG/PNG via Kroki.

    Args:
        diagram_definition: PlantUML source (without @startuml/@enduml wrappers).
        output_format: "svg" or "png".

    Returns:
        Dict with keys: diagram_source, output_format, image_data (base64), url.
    """
    source = diagram_definition
    if not source.strip().startswith("@start"):
        source = f"@startuml\n{source}\n@enduml"

    try:
        import zlib

        compressed = zlib.compress(source.encode("utf-8"), 9)
        encoded = base64.urlsafe_b64encode(compressed).decode()
        url = f"{_KROKI_API}/plantuml/{output_format}/{encoded}"

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            image_data = base64.b64encode(resp.content).decode()

        return {
            "diagram_source": source,
            "format": "plantuml",
            "output_format": output_format,
            "image_data": image_data,
            "url": url,
            "content_type": "image/svg+xml" if output_format == "svg" else "image/png",
        }
    except Exception as exc:
        logger.warning("PlantUML render failed, returning source only: %s", exc)
        return {
            "diagram_source": source,
            "format": "plantuml",
            "output_format": "text",
            "image_data": None,
            "note": str(exc),
        }


async def annotate_existing_diagram(
    image_data: str,
    annotations: list[dict[str, Any]],
    output_format: OutputFormat = "png",
) -> dict[str, Any]:
    """Add text and arrow annotations to an existing diagram image.

    Args:
        image_data: Base64-encoded PNG or SVG image.
        annotations: List of annotation dicts, each with keys:
            x (float), y (float), text (str), style (str, optional).
        output_format: Output format ("png").

    Returns:
        Dict with annotated image_data (base64) and annotation_count.
    """
    try:
        import io

        from PIL import Image, ImageDraw, ImageFont  # type: ignore

        img_bytes = base64.b64decode(image_data)
        img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
        draw = ImageDraw.Draw(img)

        for ann in annotations:
            x = int(ann.get("x", 0) * img.width)
            y = int(ann.get("y", 0) * img.height)
            text = ann.get("text", "")
            draw.text((x, y), text, fill=(255, 69, 0, 255))

        out_buf = io.BytesIO()
        img.save(out_buf, format="PNG")
        annotated_b64 = base64.b64encode(out_buf.getvalue()).decode()

        return {
            "image_data": annotated_b64,
            "annotation_count": len(annotations),
            "output_format": "png",
        }
    except Exception as exc:
        logger.error("Diagram annotation failed: %s", exc)
        return {"error": str(exc), "image_data": image_data}


def build_system_context_mermaid(
    system_name: str,
    users: list[str],
    external_systems: list[str],
) -> str:
    """Generate a C4 System Context Mermaid diagram source."""
    lines = [
        "C4Context",
        f'  title System Context — {system_name}',
    ]
    for user in users:
        uid = user.replace(" ", "_")
        lines.append(f'  Person({uid}, "{user}")')
    lines.append(f'  System(MainSystem, "{system_name}", "The system under design")')
    for ext in external_systems:
        eid = ext.replace(" ", "_")
        lines.append(f'  System_Ext({eid}, "{ext}")')
    for user in users:
        uid = user.replace(" ", "_")
        lines.append(f'  Rel({uid}, MainSystem, "Uses")')
    for ext in external_systems:
        eid = ext.replace(" ", "_")
        lines.append(f'  Rel(MainSystem, {eid}, "Integrates with")')
    return "\n".join(lines)


def build_container_diagram_mermaid(
    system_name: str,
    containers: list[dict[str, str]],
    relationships: list[dict[str, str]],
) -> str:
    """Generate a C4 Container diagram Mermaid source.

    Args:
        system_name: The system name.
        containers: List of dicts with keys: id, name, tech, description.
        relationships: List of dicts with keys: from, to, label.
    """
    lines = [
        "C4Container",
        f'  title Container Diagram — {system_name}',
    ]
    for c in containers:
        cid = c.get("id", c["name"].replace(" ", "_"))
        lines.append(
            f'  Container({cid}, "{c["name"]}", "{c.get("tech", "")}", "{c.get("description", "")}")'
        )
    for r in relationships:
        lines.append(f'  Rel({r["from"]}, {r["to"]}, "{r.get("label", "")}")')
    return "\n".join(lines)
