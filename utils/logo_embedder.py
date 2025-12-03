# -*- coding: utf-8 -*-
"""
Logo Embedder for PDF Generation.

Embeds logo images as base64 data URIs in HTML to ensure they render
correctly when the HTML is sent to an external PDF service.

Includes optimize_base64_image() for:
- PNG→WebP conversion (quality 70-80, typically 50-70% size reduction)
- SVG minification (whitespace removal, attribute compaction)
"""
from __future__ import annotations

import base64
import io
import logging
import os
import re
from pathlib import Path
from typing import Dict, Optional, Tuple

log = logging.getLogger(__name__)

# --- Image Optimization ---

# Try to import Pillow for PNG→WebP conversion
try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    log.debug("[LOGO-OPTIMIZE] Pillow not available, PNG→WebP disabled")


def optimize_base64_image(
    data: bytes,
    mime_type: str,
    webp_quality: int = 75,
    max_dimension: Optional[int] = 400
) -> Tuple[bytes, str]:
    """
    Optimize image data for smaller base64 embedding.

    PNG/JPEG → WebP conversion (50-70% size reduction)
    SVG → Minification (whitespace removal)

    Args:
        data: Raw image bytes
        mime_type: Original MIME type (image/png, image/svg+xml, etc.)
        webp_quality: WebP quality 0-100 (default 75)
        max_dimension: Max width/height in pixels (None = no resize)

    Returns:
        Tuple of (optimized_bytes, new_mime_type)
    """
    original_size = len(data)

    # --- SVG Minification ---
    if mime_type == "image/svg+xml":
        try:
            svg_text = data.decode("utf-8")
            optimized = _minify_svg(svg_text)
            optimized_bytes = optimized.encode("utf-8")
            new_size = len(optimized_bytes)
            if new_size < original_size:
                log.debug("[LOGO-OPTIMIZE] SVG minified: %d → %d bytes (%.0f%%)",
                         original_size, new_size, (1 - new_size/original_size) * 100)
                return optimized_bytes, mime_type
            return data, mime_type
        except Exception as e:
            log.warning("[LOGO-OPTIMIZE] SVG minification failed: %s", e)
            return data, mime_type

    # --- PNG/JPEG → WebP ---
    if PILLOW_AVAILABLE and mime_type in ("image/png", "image/jpeg", "image/jpg"):
        try:
            img = Image.open(io.BytesIO(data))

            # Resize if too large
            if max_dimension and (img.width > max_dimension or img.height > max_dimension):
                img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
                log.debug("[LOGO-OPTIMIZE] Resized to %dx%d", img.width, img.height)

            # Convert to WebP
            output = io.BytesIO()
            # Handle transparency for PNG
            if img.mode in ("RGBA", "LA", "P"):
                img.save(output, format="WEBP", quality=webp_quality, lossless=False)
            else:
                img.save(output, format="WEBP", quality=webp_quality)

            optimized_bytes = output.getvalue()
            new_size = len(optimized_bytes)

            # Only use WebP if actually smaller
            if new_size < original_size:
                log.debug("[LOGO-OPTIMIZE] %s → WebP: %d → %d bytes (%.0f%%)",
                         mime_type, original_size, new_size, (1 - new_size/original_size) * 100)
                return optimized_bytes, "image/webp"
            else:
                log.debug("[LOGO-OPTIMIZE] WebP not smaller, keeping original")
                return data, mime_type

        except Exception as e:
            log.warning("[LOGO-OPTIMIZE] PNG/JPEG→WebP failed: %s", e)
            return data, mime_type

    # No optimization possible
    return data, mime_type


def _minify_svg(svg: str) -> str:
    """
    Minify SVG by removing unnecessary whitespace and comments.

    - Remove XML comments
    - Collapse whitespace between tags
    - Remove whitespace inside tags
    - Strip leading/trailing whitespace
    """
    # Remove XML comments
    svg = re.sub(r"<!--.*?-->", "", svg, flags=re.DOTALL)

    # Remove newlines and excess whitespace between tags
    svg = re.sub(r">\s+<", "><", svg)

    # Collapse multiple spaces to single space
    svg = re.sub(r"\s{2,}", " ", svg)

    # Remove whitespace before closing tags
    svg = re.sub(r"\s+/>", "/>", svg)

    # Remove whitespace after opening tag bracket
    svg = re.sub(r"<\s+", "<", svg)

    # Remove whitespace before closing tag bracket
    svg = re.sub(r"\s+>", ">", svg)

    return svg.strip()

# Default logo files to embed
DEFAULT_LOGOS = [
    "ki-sicherheit-logo.webp",
    "tuev-logo-transparent.webp",
    "ki-ready-2025.webp",
    "dsgvo.svg",
    "eu-ai.svg",
]

def get_logo_base64_map(
    template_dir: str = "templates",
    optimize: bool = True,
    webp_quality: int = 75
) -> Dict[str, str]:
    """
    Load logo files and convert to base64 data URIs.

    Args:
        template_dir: Directory containing logo files
        optimize: Whether to optimize images (PNG→WebP, SVG minify)
        webp_quality: WebP quality for PNG/JPEG conversion (0-100)

    Returns:
        Dictionary mapping filename to base64 data URI
    """
    logo_map: Dict[str, str] = {}
    template_path = Path(template_dir)
    total_original = 0
    total_optimized = 0

    for logo_name in DEFAULT_LOGOS:
        logo_path = template_path / logo_name
        if not logo_path.exists():
            # Try assets subdirectory
            logo_path = template_path / "assets" / logo_name

        if logo_path.exists():
            try:
                with open(logo_path, "rb") as f:
                    data = f.read()

                    # Determine MIME type
                    ext = logo_path.suffix.lower()
                    mime_type = {
                        ".webp": "image/webp",
                        ".png": "image/png",
                        ".jpg": "image/jpeg",
                        ".jpeg": "image/jpeg",
                        ".svg": "image/svg+xml",
                    }.get(ext, "image/webp")

                    original_size = len(data)
                    total_original += original_size

                    # Optimize if enabled
                    if optimize:
                        data, mime_type = optimize_base64_image(
                            data, mime_type, webp_quality=webp_quality
                        )

                    total_optimized += len(data)
                    b64 = base64.b64encode(data).decode("utf-8")

                    data_uri = f"data:{mime_type};base64,{b64}"
                    logo_map[logo_name] = data_uri
                    log.debug(f"[LOGO-EMBED] Loaded {logo_name}: {len(b64)} chars base64")
            except Exception as e:
                log.warning(f"[LOGO-EMBED] Failed to load {logo_name}: {e}")
        else:
            log.warning(f"[LOGO-EMBED] Logo not found: {logo_name}")

    if optimize and total_original > 0:
        savings = (1 - total_optimized / total_original) * 100
        log.info(f"[LOGO-EMBED] Loaded {len(logo_map)} logos, optimized {total_original}→{total_optimized} bytes ({savings:.0f}% saved)")
    else:
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
