# -*- coding: utf-8 -*-
"""
Logo Embedder for PDF Generation.

Embeds logo images as base64 data URIs in HTML to ensure they render
correctly when the HTML is sent to an external PDF service.

Version: 2.0.0 PDF-SLIMDOWN

Includes optimize_base64_image() for:
- Lossless WebP conversion (40-60% size reduction)
- 8-bit color depth reduction
- PNG channel stripping
- SVG minification (whitespace removal, attribute compaction)
- Max logo size enforcement (40-60kB each)
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

# --- Configuration ---
MAX_LOGO_SIZE_BYTES = 50 * 1024  # 50kB max per logo (target: 40-60kB)
MAX_LOGO_DIMENSION = 300  # Max width/height for logos in PDF

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
    max_dimension: Optional[int] = None,
    lossless: bool = True
) -> Tuple[bytes, str]:
    """
    Optimize image data for smaller base64 embedding.

    PNG/JPEG → Lossless WebP conversion (40-60% size reduction)
    SVG → Minification (whitespace removal)
    8-bit color depth reduction for smaller files
    Max size enforcement (40-60kB)

    Args:
        data: Raw image bytes
        mime_type: Original MIME type (image/png, image/svg+xml, etc.)
        webp_quality: WebP quality 0-100 (default 75, used if lossless fails size limit)
        max_dimension: Max width/height in pixels (default: MAX_LOGO_DIMENSION)
        lossless: Use lossless WebP compression (default True)

    Returns:
        Tuple of (optimized_bytes, new_mime_type)
    """
    original_size = len(data)
    if max_dimension is None:
        max_dimension = MAX_LOGO_DIMENSION

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

    # --- PNG/JPEG → Lossless WebP with 8-bit color depth ---
    if PILLOW_AVAILABLE and mime_type in ("image/png", "image/jpeg", "image/jpg", "image/webp"):
        try:
            # B42-FIX: Convert WebP → PNG for data URI embedding.
            # WebP data URIs render correctly when loaded as files in Chromium,
            # but can fail as inline data URIs in Puppeteer PDF rendering
            # (badges show alt-text instead of image). PNG data URIs are
            # universally supported. R2 template works because its rendering
            # pipeline differs from R1's.
            if mime_type == "image/webp":
                img: Image.Image = Image.open(io.BytesIO(data))
                # Resize if too large
                if max_dimension and (img.width > max_dimension or img.height > max_dimension):
                    img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
                output = io.BytesIO()
                img.save(output, format="PNG", optimize=True)
                png_data = output.getvalue()
                log.info("[LOGO-OPTIMIZE] WebP→PNG for data URI: %d → %d bytes", original_size, len(png_data))
                return png_data, "image/png"

            img = Image.open(io.BytesIO(data))

            # Resize if too large
            if max_dimension and (img.width > max_dimension or img.height > max_dimension):
                img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
                log.debug("[LOGO-OPTIMIZE] Resized to %dx%d", img.width, img.height)

            # Reduce color depth to 8-bit (palette mode) for smaller files
            # Only for images without critical transparency
            original_mode = img.mode
            if img.mode == "RGBA":
                # Keep RGBA for transparency, but try to quantize
                img_quantized = img.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
                img_quantized = img_quantized.convert("RGBA")
                img = img_quantized
            elif img.mode in ("RGB", "L"):
                # Convert to palette mode (8-bit)
                img = img.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
                img = img.convert("RGB")

            # Try lossless WebP first
            output = io.BytesIO()
            if lossless:
                img.save(output, format="WEBP", lossless=True, quality=100)
            else:
                img.save(output, format="WEBP", quality=webp_quality, lossless=False)

            optimized_bytes = output.getvalue()
            new_size = len(optimized_bytes)

            # If lossless is too large, fall back to lossy with quality reduction
            if new_size > MAX_LOGO_SIZE_BYTES and lossless:
                log.debug("[LOGO-OPTIMIZE] Lossless too large (%d bytes), trying lossy", new_size)
                output = io.BytesIO()
                img.save(output, format="WEBP", quality=webp_quality, lossless=False)
                optimized_bytes = output.getvalue()
                new_size = len(optimized_bytes)

                # If still too large, reduce quality further
                if new_size > MAX_LOGO_SIZE_BYTES:
                    for quality in [60, 50, 40]:
                        output = io.BytesIO()
                        img.save(output, format="WEBP", quality=quality, lossless=False)
                        optimized_bytes = output.getvalue()
                        new_size = len(optimized_bytes)
                        if new_size <= MAX_LOGO_SIZE_BYTES:
                            log.debug("[LOGO-OPTIMIZE] Reduced quality to %d to meet size limit", quality)
                            break

            # Only use WebP if actually smaller
            if new_size < original_size:
                log.debug("[LOGO-OPTIMIZE] %s → WebP: %d → %d bytes (%.0f%% saved)",
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
    "ki-sicherheit-logo-small.png",
    "tuev-logo-transparent.png",
    "KI-READY-2025-badge.png",
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

    # FIX-B: Resolve relative paths against project root to avoid CWD issues
    # on Railway (worker processes may have different CWD than expected).
    if not template_path.is_absolute():
        project_root = Path(__file__).resolve().parent.parent
        template_path = project_root / template_path
    template_path = template_path.resolve()
    log.info("[LOGO-EMBED] Resolved template_dir: %s (exists=%s)", template_path, template_path.exists())

    # FIX-D3: List files in template_dir for diagnostics
    if template_path.exists():
        try:
            _files = sorted(f.name for f in template_path.iterdir() if f.is_file())
            log.info("[LOGO-EMBED] Files in template_dir: %s", _files)
        except Exception as _e:
            log.warning("[LOGO-EMBED] Cannot list template_dir: %s", _e)

    total_original = 0
    total_optimized = 0

    for logo_name in DEFAULT_LOGOS:
        logo_path = template_path / logo_name
        if not logo_path.exists():
            # Try assets subdirectory
            logo_path = template_path / "assets" / logo_name

        log.info("[LOGO-EMBED] Looking for: %s at %s (exists=%s, size=%s)",
                 logo_name, logo_path,
                 logo_path.exists(),
                 logo_path.stat().st_size if logo_path.exists() else 'N/A')

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
                    log.info("[LOGO-EMBED] Embedded %s as base64 (%s, %d bytes)", logo_name, mime_type, len(data))
            except Exception as e:
                log.warning(f"[LOGO-EMBED] Failed to load {logo_name}: {e}")
        else:
            log.warning("[LOGO-EMBED] SKIPPED %s: file not found at %s", logo_name, logo_path)

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
    log.info("[LOGO-EMBED] Called with template_dir=%s (exists=%s)",
             template_dir, Path(template_dir).exists())
    logo_map = get_logo_base64_map(template_dir)

    if not logo_map:
        log.warning("[LOGO-EMBED] No logos loaded, HTML unchanged")
        return html

    modified_html = html
    replacements = 0

    # Map new PNG filenames to their old WebP equivalents for backward compat
    _png_to_webp_compat = {
        "ki-sicherheit-logo-small.png": ["ki-sicherheit-logo.webp", "ki-sicherheit-logo.png"],
        "tuev-logo-transparent.png": ["tuev-logo-transparent.webp"],
        "KI-READY-2025-badge.png": ["ki-ready-2025.webp", "KI-READY-2025.webp", "KI-READY-2025.png"],
    }

    for filename, data_uri in logo_map.items():
        # Match various src patterns (current name + old WebP names)
        alt_names = _png_to_webp_compat.get(filename, [])
        all_names = [filename] + alt_names
        patterns = []
        for name in all_names:
            patterns.append(f'src="{name}"')
            patterns.append(f"src='{name}'")

        for pattern in patterns:
            found = pattern in modified_html
            log.info("[LOGO-EMBED] Pattern '%s' found in HTML: %s", pattern[:60], found)
            if found:
                replacement = f'src="{data_uri[:50]}..."'
                modified_html = modified_html.replace(pattern, f'src="{data_uri}"')
                replacements += 1

    log.info("[LOGO-EMBED] Result: %d of %d logos embedded", replacements, len(DEFAULT_LOGOS))
    if replacements < len(DEFAULT_LOGOS):
        # B41: Warn about un-embedded logos so they get caught by embed_all_images_in_html
        missing = [f for f in DEFAULT_LOGOS if f'src="{f}"' in modified_html or f"src='{f}'" in modified_html]
        if missing:
            log.warning("[LOGO-EMBED] Still un-embedded after pass 1: %s", missing)
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

    # Resolve relative paths against project root (same as get_logo_base64_map)
    if not template_path.is_absolute():
        project_root = Path(__file__).resolve().parent.parent
        template_path = project_root / template_path
    template_path = template_path.resolve()

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

                    ext = file_path.suffix.lower()
                    mime_type = {
                        ".webp": "image/webp",
                        ".png": "image/png",
                        ".jpg": "image/jpeg",
                        ".jpeg": "image/jpeg",
                        ".svg": "image/svg+xml",
                        ".gif": "image/gif",
                    }.get(ext, "application/octet-stream")

                    # WEBP-SAFETY-NET: Convert WebP files to PNG for Puppeteer compat
                    if ext == ".webp" and PILLOW_AVAILABLE:
                        try:
                            data, mime_type = optimize_base64_image(data, mime_type)
                            log.info("[WEBP-SAFETY-NET] Converted %s to PNG data URI (%d chars)",
                                     file_path.name, len(data))
                        except Exception as conv_err:
                            log.warning("[WEBP-SAFETY-NET] Failed to convert %s: %s", src, conv_err)

                    b64 = base64.b64encode(data).decode("utf-8")
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


def convert_webp_paths_to_png_base64(html: str, base_dir: str = None) -> str:
    """
    Safety net: Convert any remaining <img src="...webp"> file paths
    to PNG base64 data URIs for Puppeteer compatibility.

    This complements optimize_base64_image() which handles base64-embedded WebP.
    This function handles FILE PATH-referenced WebP images.
    """
    if not PILLOW_AVAILABLE:
        log.warning("[WEBP-SAFETY-NET] Pillow not available, skipping WebP conversion")
        return html

    # Resolve base_dir
    if base_dir:
        base_path = Path(base_dir)
        if not base_path.is_absolute():
            project_root = Path(__file__).resolve().parent.parent
            base_path = project_root / base_path
        base_path = base_path.resolve()
    else:
        base_path = Path(__file__).resolve().parent.parent / "templates"

    def replace_webp_src(match):
        full_tag = match.group(0)
        src = match.group(1)

        # Skip data URIs (handled by optimize_base64_image)
        if src.startswith("data:"):
            return full_tag

        # Skip non-webp files
        if not src.lower().endswith(".webp"):
            return full_tag

        try:
            # Resolve path
            file_path = Path(src)
            if not file_path.is_absolute():
                file_path = base_path / file_path

            if not file_path.exists():
                # Try common asset directories
                for try_dir in ["", "static", "assets", "images", "badges"]:
                    alt_path = base_path / try_dir / Path(src).name if try_dir else base_path / Path(src).name
                    if alt_path.exists():
                        file_path = alt_path
                        break

            if not file_path.exists():
                log.warning("[WEBP-SAFETY-NET] File not found: %s", src)
                return full_tag

            # Convert WebP -> PNG in memory
            img = Image.open(file_path).convert("RGBA")

            # Resize if too large (badges shouldn't be > 200px)
            max_h = 200
            if img.size[1] > max_h:
                ratio = max_h / img.size[1]
                img = img.resize((int(img.size[0] * ratio), max_h), Image.LANCZOS)

            buf = io.BytesIO()
            img.save(buf, format="PNG", optimize=True)
            b64 = base64.b64encode(buf.getvalue()).decode()

            new_src = f"data:image/png;base64,{b64}"
            log.info("[WEBP-SAFETY-NET] Converted %s to PNG data URI (%d chars)",
                     file_path.name, len(b64))
            return full_tag.replace(src, new_src)

        except Exception as e:
            log.warning("[WEBP-SAFETY-NET] Failed to convert %s: %s", src, e)
            return full_tag

    # Match <img ... src="...webp"> tags
    pattern = r'<img[^>]+src=["\']([^"\']+\.webp)["\'][^>]*>'
    return re.sub(pattern, replace_webp_src, html, flags=re.IGNORECASE)
