# -*- coding: utf-8 -*-
"""
Logo Embedder for PDF Generation.

Embeds logo images as base64 data URIs in HTML to ensure they render
correctly when the HTML is sent to an external PDF service.
"""
from __future__ import annotations

import base64
import logging
import os
import re
from pathlib import Path
from typing import Dict

log = logging.getLogger(__name__)

# Default logo files to embed
DEFAULT_LOGOS = [
    "ki-sicherheit-logo.webp",
    "tuev-logo-transparent.webp",
    "ki-ready-2025.webp",
]

def get_logo_base64_map(template_dir: str = "templates") -> Dict[str, str]:
    """
    Load logo files and convert to base64 data URIs.

    Args:
        template_dir: Directory containing logo files

    Returns:
        Dictionary mapping filename to base64 data URI
    """
    logo_map: Dict[str, str] = {}
    template_path = Path(template_dir)

    for logo_name in DEFAULT_LOGOS:
        logo_path = template_path / logo_name
        if not logo_path.exists():
            # Try assets subdirectory
            logo_path = template_path / "assets" / logo_name

        if logo_path.exists():
            try:
                with open(logo_path, "rb") as f:
                    data = f.read()
                    b64 = base64.b64encode(data).decode("utf-8")

                    # Determine MIME type
                    ext = logo_path.suffix.lower()
                    mime_type = {
                        ".webp": "image/webp",
                        ".png": "image/png",
                        ".jpg": "image/jpeg",
                        ".jpeg": "image/jpeg",
                        ".svg": "image/svg+xml",
                    }.get(ext, "image/webp")

                    data_uri = f"data:{mime_type};base64,{b64}"
                    logo_map[logo_name] = data_uri
                    log.debug(f"[LOGO-EMBED] Loaded {logo_name}: {len(b64)} chars base64")
            except Exception as e:
                log.warning(f"[LOGO-EMBED] Failed to load {logo_name}: {e}")
        else:
            log.warning(f"[LOGO-EMBED] Logo not found: {logo_name}")

    log.info(f"[LOGO-EMBED] Loaded {len(logo_map)} logos for embedding")
    return logo_map


def embed_logos_in_html(html: str, template_dir: str = "templates") -> str:
    """
    Replace logo src attributes with base64 data URIs.

    Args:
        html: HTML string with relative logo paths
        template_dir: Directory containing logo files

    Returns:
        HTML with embedded base64 logos
    """
    logo_map = get_logo_base64_map(template_dir)

    if not logo_map:
        log.warning("[LOGO-EMBED] No logos loaded, HTML unchanged")
        return html

    modified_html = html
    replacements = 0

    for filename, data_uri in logo_map.items():
        # Match various src patterns
        patterns = [
            f'src="{filename}"',
            f"src='{filename}'",
            f'src="{filename.replace(".webp", "")}"',  # Without extension
        ]

        for pattern in patterns:
            if pattern in modified_html:
                replacement = f'src="{data_uri}"'
                modified_html = modified_html.replace(pattern, replacement)
                replacements += 1
                log.debug(f"[LOGO-EMBED] Replaced: {pattern[:50]}...")

    log.info(f"[LOGO-EMBED] Made {replacements} logo replacements in HTML")
    return modified_html


def embed_all_images_in_html(html: str, template_dir: str = "templates") -> str:
    """
    Find and embed all local images referenced in HTML.

    This function scans for img tags with local file references
    and converts them to base64 data URIs.

    Args:
        html: HTML string
        template_dir: Base directory for resolving relative paths

    Returns:
        HTML with embedded images
    """
    template_path = Path(template_dir)
    modified_html = html

    # Find all img src attributes
    img_pattern = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)
    matches = img_pattern.findall(html)

    embedded_count = 0
    for src in matches:
        # Skip already embedded images and external URLs
        if src.startswith("data:") or src.startswith("http"):
            continue

        # Try to find the file
        file_path = template_path / src
        if not file_path.exists():
            file_path = template_path / "assets" / src

        if file_path.exists() and file_path.is_file():
            try:
                with open(file_path, "rb") as f:
                    data = f.read()
                    b64 = base64.b64encode(data).decode("utf-8")

                    ext = file_path.suffix.lower()
                    mime_type = {
                        ".webp": "image/webp",
                        ".png": "image/png",
                        ".jpg": "image/jpeg",
                        ".jpeg": "image/jpeg",
                        ".svg": "image/svg+xml",
                        ".gif": "image/gif",
                    }.get(ext, "application/octet-stream")

                    data_uri = f"data:{mime_type};base64,{b64}"

                    # Replace in HTML
                    modified_html = modified_html.replace(f'src="{src}"', f'src="{data_uri}"')
                    modified_html = modified_html.replace(f"src='{src}'", f'src="{data_uri}"')
                    embedded_count += 1
                    log.debug(f"[IMAGE-EMBED] Embedded: {src}")
            except Exception as e:
                log.warning(f"[IMAGE-EMBED] Failed to embed {src}: {e}")

    log.info(f"[IMAGE-EMBED] Embedded {embedded_count} images in HTML")
    return modified_html
