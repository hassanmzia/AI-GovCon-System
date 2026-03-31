"""
Template rendering service — fills {{placeholder}} variables in DOCX templates
using docxtpl (Jinja2-in-Word) and returns rendered documents.

Supports:
  - DOCX templates with {{ variable }} placeholders (via docxtpl)
  - Plain-text/contract templates with {{variable}} string substitution
  - Batch rendering from deal/proposal context
"""

import io
import logging
import os
import re
import tempfile
from typing import Any

from django.core.files.base import ContentFile

logger = logging.getLogger("knowledge_vault.template_renderer")


def render_docx_template(template_file, context: dict[str, Any]) -> bytes:
    """
    Render a DOCX template with Jinja2 placeholders using docxtpl.

    Args:
        template_file: Django FieldFile or file path to the .docx template.
        context: Dict of variable values to fill in the template.

    Returns:
        Rendered DOCX file as bytes.
    """
    try:
        from docxtpl import DocxTemplate
    except ImportError:
        logger.error("docxtpl not installed. Install with: pip install docxtpl")
        raise ImportError(
            "docxtpl is required for DOCX template rendering. "
            "Install it with: pip install docxtpl"
        )

    # Read template into a temp file (docxtpl needs a file path or file-like)
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        if hasattr(template_file, "read"):
            # Django FieldFile or file-like
            template_file.seek(0)
            tmp.write(template_file.read())
        elif isinstance(template_file, (str, os.PathLike)):
            with open(template_file, "rb") as f:
                tmp.write(f.read())
        else:
            tmp.write(template_file)
        tmp_path = tmp.name

    try:
        doc = DocxTemplate(tmp_path)
        doc.render(context)

        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()
    finally:
        os.unlink(tmp_path)


def render_text_template(content: str, context: dict[str, Any]) -> str:
    """
    Render a plain-text or contract template with {{variable}} placeholders.

    Args:
        content: Template string with {{variable}} placeholders.
        context: Dict of variable values.

    Returns:
        Rendered string with placeholders filled.
    """
    result = content
    for key, value in context.items():
        result = result.replace("{{" + key + "}}", str(value))
    return result


def extract_variables_from_docx(template_file) -> list[dict[str, str]]:
    """
    Extract Jinja2 variable names from a DOCX template.

    Returns list of variable dicts: [{"name": "var_name", "label": "Var Name", "default": ""}]
    """
    try:
        from docxtpl import DocxTemplate
    except ImportError:
        return []

    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        if hasattr(template_file, "read"):
            template_file.seek(0)
            tmp.write(template_file.read())
        else:
            with open(template_file, "rb") as f:
                tmp.write(f.read())
        tmp_path = tmp.name

    try:
        doc = DocxTemplate(tmp_path)
        # docxtpl uses undeclared_template_variables to find placeholders
        variables = doc.get_undeclared_template_variables()

        result = []
        for var_name in sorted(variables):
            label = var_name.replace("_", " ").title()
            result.append({"name": var_name, "label": label, "default": ""})
        return result
    except Exception as exc:
        logger.warning("Failed to extract variables from template: %s", exc)
        return []
    finally:
        os.unlink(tmp_path)


def extract_variables_from_text(content: str) -> list[dict[str, str]]:
    """Extract {{variable}} placeholders from text content."""
    pattern = re.compile(r"\{\{(\w+)\}\}")
    variables = sorted(set(pattern.findall(content)))
    return [
        {"name": v, "label": v.replace("_", " ").title(), "default": ""}
        for v in variables
    ]


def render_template_to_file(template_record, context: dict[str, Any]) -> ContentFile:
    """
    High-level: given a DocumentTemplate model instance and context,
    render and return a Django ContentFile ready for download or storage.
    """
    from apps.knowledge_vault.models import DocumentTemplate

    if template_record.file_format == "docx" and template_record.file:
        rendered_bytes = render_docx_template(template_record.file, context)
        filename = f"rendered_{template_record.name[:50]}.docx"
        return ContentFile(rendered_bytes, name=filename)

    elif template_record.file_format == "txt":
        # For text-based templates, read file content and do substitution
        if template_record.file:
            template_record.file.seek(0)
            content = template_record.file.read().decode("utf-8", errors="replace")
        else:
            content = ""
        rendered = render_text_template(content, context)
        filename = f"rendered_{template_record.name[:50]}.txt"
        return ContentFile(rendered.encode("utf-8"), name=filename)

    else:
        raise ValueError(
            f"Rendering not supported for format: {template_record.file_format}. "
            "Only DOCX and TXT templates support variable substitution."
        )
