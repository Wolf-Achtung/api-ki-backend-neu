# -*- coding: utf-8 -*-
"""
Sprint G12: PDF Guard

Protects PDF generation from resource exhaustion:
- HTML size limits
- Image count/budget limits
- Table count limits
- Memory protection

Version: 1.0.0 (Sprint G12)
"""
from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)

# =============================================================================
# ENV CONFIGURATION
# =============================================================================

PDF_GUARD_ENABLED = os.getenv("PDF_GUARD_ENABLED", "1").lower() in ("1", "true", "yes")
PDF_MAX_HTML_MB = float(os.getenv("PDF_MAX_HTML_MB", "1.2"))
PDF_MAX_TABLES = int(os.getenv("PDF_MAX_TABLES", "30"))
PDF_MAX_IMAGES = int(os.getenv("PDF_MAX_IMAGES", "20"))
PDF_MAX_LOGOS = int(os.getenv("PDF_MAX_LOGOS", "5"))
PDF_FAIL_ON_OVERSIZE = os.getenv("PDF_FAIL_ON_OVERSIZE", "0").lower() in ("1", "true", "yes")
PDF_TRUNCATE_ON_OVERSIZE = os.getenv("PDF_TRUNCATE_ON_OVERSIZE", "1").lower() in ("1", "true", "yes")


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class PDFGuardIssue:
    """A single guard issue."""
    code: str
    severity: str  # error, warning, info, truncated
    message: str
    limit: Optional[int] = None
    actual: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
        }
        if self.limit is not None:
            result["limit"] = self.limit
        if self.actual is not None:
            result["actual"] = self.actual
        return result


@dataclass
class PDFGuardResult:
    """Result of PDF guard check."""
    allowed: bool = True
    html_size_bytes: int = 0
    table_count: int = 0
    image_count: int = 0
    logo_count: int = 0
    issues: List[PDFGuardIssue] = field(default_factory=list)
    truncated: bool = False
    truncated_html: Optional[str] = None

    def add_issue(
        self,
        code: str,
        severity: str,
        message: str,
        limit: Optional[int] = None,
        actual: Optional[int] = None,
    ) -> None:
        self.issues.append(PDFGuardIssue(
            code=code,
            severity=severity,
            message=message,
            limit=limit,
            actual=actual,
        ))
        if severity == "error":
            self.allowed = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "html_size_bytes": self.html_size_bytes,
            "html_size_mb": round(self.html_size_bytes / (1024 * 1024), 3),
            "table_count": self.table_count,
            "image_count": self.image_count,
            "logo_count": self.logo_count,
            "truncated": self.truncated,
            "issues": [i.to_dict() for i in self.issues],
        }


# =============================================================================
# PDF GUARD IMPLEMENTATION
# =============================================================================

class PDFGuard:
    """
    Guards PDF generation against resource exhaustion.

    Checks:
    - HTML payload size
    - Number of tables
    - Number of images
    - Number of logos
    - Provides truncation options
    """

    # Regex patterns for content detection
    TABLE_PATTERN = re.compile(r'<table\b', re.IGNORECASE)
    IMAGE_PATTERN = re.compile(r'<img\b', re.IGNORECASE)
    SVG_PATTERN = re.compile(r'<svg\b', re.IGNORECASE)
    LOGO_PATTERN = re.compile(r'(?:logo|brand|emblem)', re.IGNORECASE)

    # Patterns for sections that can be truncated
    SECTION_PATTERN = re.compile(
        r'(<div[^>]*class="[^"]*section[^"]*"[^>]*>)(.*?)(</div>)',
        re.IGNORECASE | re.DOTALL
    )

    def __init__(
        self,
        max_html_mb: float = PDF_MAX_HTML_MB,
        max_tables: int = PDF_MAX_TABLES,
        max_images: int = PDF_MAX_IMAGES,
        max_logos: int = PDF_MAX_LOGOS,
    ):
        self.max_html_bytes = int(max_html_mb * 1024 * 1024)
        self.max_tables = max_tables
        self.max_images = max_images
        self.max_logos = max_logos

    def check(self, html: str) -> PDFGuardResult:
        """
        Check HTML content against limits.

        Args:
            html: HTML string to check

        Returns:
            PDFGuardResult with metrics and issues
        """
        result = PDFGuardResult()

        if not PDF_GUARD_ENABLED:
            result.add_issue("GUARD_DISABLED", "info", "PDF guard is disabled")
            return result

        # Measure size
        result.html_size_bytes = len(html.encode('utf-8'))

        # Count elements
        result.table_count = len(self.TABLE_PATTERN.findall(html))
        result.image_count = len(self.IMAGE_PATTERN.findall(html)) + len(self.SVG_PATTERN.findall(html))
        result.logo_count = len(self.LOGO_PATTERN.findall(html))

        # Check limits
        self._check_size(result, html)
        self._check_tables(result)
        self._check_images(result)
        self._check_logos(result)

        # Log result
        if not result.allowed:
            log.error(
                "[G12-PDFGuard] Content rejected: size=%dKB tables=%d images=%d",
                result.html_size_bytes // 1024,
                result.table_count,
                result.image_count,
            )
        elif result.issues:
            log.warning(
                "[G12-PDFGuard] Warnings: size=%dKB tables=%d images=%d",
                result.html_size_bytes // 1024,
                result.table_count,
                result.image_count,
            )

        return result

    def _check_size(self, result: PDFGuardResult, html: str) -> None:
        """Check HTML size limit."""
        if result.html_size_bytes > self.max_html_bytes:
            size_mb = result.html_size_bytes / (1024 * 1024)
            max_mb = self.max_html_bytes / (1024 * 1024)

            if PDF_FAIL_ON_OVERSIZE:
                result.add_issue(
                    "HTML_TOO_LARGE",
                    "error",
                    f"HTML size ({size_mb:.2f}MB) exceeds limit ({max_mb:.2f}MB)",
                    limit=self.max_html_bytes,
                    actual=result.html_size_bytes,
                )
            else:
                result.add_issue(
                    "HTML_SIZE_WARNING",
                    "warning",
                    f"HTML size ({size_mb:.2f}MB) exceeds recommended limit ({max_mb:.2f}MB)",
                    limit=self.max_html_bytes,
                    actual=result.html_size_bytes,
                )

                # Try truncation if enabled
                if PDF_TRUNCATE_ON_OVERSIZE:
                    truncated = self._truncate_html(html, self.max_html_bytes)
                    if truncated and len(truncated.encode('utf-8')) < result.html_size_bytes:
                        result.truncated = True
                        result.truncated_html = truncated
                        result.add_issue(
                            "HTML_TRUNCATED",
                            "truncated",
                            "HTML was truncated to fit size limit",
                        )

    def _check_tables(self, result: PDFGuardResult) -> None:
        """Check table count limit."""
        if result.table_count > self.max_tables:
            if PDF_FAIL_ON_OVERSIZE:
                result.add_issue(
                    "TOO_MANY_TABLES",
                    "error",
                    f"Table count ({result.table_count}) exceeds limit ({self.max_tables})",
                    limit=self.max_tables,
                    actual=result.table_count,
                )
            else:
                result.add_issue(
                    "TABLE_COUNT_WARNING",
                    "warning",
                    f"Table count ({result.table_count}) exceeds recommended limit ({self.max_tables})",
                    limit=self.max_tables,
                    actual=result.table_count,
                )

    def _check_images(self, result: PDFGuardResult) -> None:
        """Check image count limit."""
        if result.image_count > self.max_images:
            if PDF_FAIL_ON_OVERSIZE:
                result.add_issue(
                    "TOO_MANY_IMAGES",
                    "error",
                    f"Image count ({result.image_count}) exceeds limit ({self.max_images})",
                    limit=self.max_images,
                    actual=result.image_count,
                )
            else:
                result.add_issue(
                    "IMAGE_COUNT_WARNING",
                    "warning",
                    f"Image count ({result.image_count}) exceeds recommended limit ({self.max_images})",
                    limit=self.max_images,
                    actual=result.image_count,
                )

    def _check_logos(self, result: PDFGuardResult) -> None:
        """Check logo count limit."""
        if result.logo_count > self.max_logos:
            result.add_issue(
                "LOGO_COUNT_WARNING",
                "warning",
                f"Logo references ({result.logo_count}) exceeds recommended limit ({self.max_logos})",
                limit=self.max_logos,
                actual=result.logo_count,
            )

    def _truncate_html(self, html: str, target_bytes: int) -> Optional[str]:
        """
        Attempt to truncate HTML to target size.

        Strategy:
        1. Find content sections that can be shortened
        2. Remove less critical content first
        3. Add truncation notice
        """
        current_size = len(html.encode('utf-8'))
        if current_size <= target_bytes:
            return html

        # Find all sections
        sections = list(self.SECTION_PATTERN.finditer(html))
        if not sections:
            # No sections to truncate, just cut the end
            return html[:target_bytes - 100] + "\n<!-- Content truncated -->\n</body></html>"

        # Calculate how much to remove
        excess = current_size - target_bytes + 1000  # Extra buffer

        # Start removing from the end, keeping structure
        truncated = html
        removed = 0

        for section in reversed(sections):
            if removed >= excess:
                break

            section_content = section.group(2)
            section_size = len(section_content.encode('utf-8'))

            # Replace section content with truncation notice
            truncated = (
                truncated[:section.start(2)] +
                '<p class="truncated">[Content shortened for PDF generation]</p>' +
                truncated[section.end(2):]
            )
            removed += section_size - 80  # Approximate size of notice

        return truncated

    def guard_and_process(self, html: str) -> tuple[str, PDFGuardResult]:
        """
        Check and optionally truncate HTML.

        Returns:
            Tuple of (processed_html, result)
        """
        result = self.check(html)

        if result.truncated and result.truncated_html:
            return result.truncated_html, result

        if not result.allowed and PDF_FAIL_ON_OVERSIZE:
            raise PDFGuardError(result)

        return html, result


class PDFGuardError(Exception):
    """Raised when PDF content exceeds limits and FAIL_ON_OVERSIZE is enabled."""

    def __init__(self, result: PDFGuardResult):
        self.result = result
        issues = [i.message for i in result.issues if i.severity == "error"]
        super().__init__(f"PDF guard rejected content: {'; '.join(issues)}")


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_guard_instance: Optional[PDFGuard] = None


def get_pdf_guard() -> PDFGuard:
    """Get singleton PDF guard instance."""
    global _guard_instance
    if _guard_instance is None:
        _guard_instance = PDFGuard()
    return _guard_instance


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def check_pdf_content(html: str) -> PDFGuardResult:
    """
    Convenience function to check PDF content.

    Args:
        html: HTML content to check

    Returns:
        PDFGuardResult
    """
    return get_pdf_guard().check(html)


def guard_pdf_content(html: str) -> tuple[str, PDFGuardResult]:
    """
    Check and optionally process PDF content.

    Args:
        html: HTML content

    Returns:
        Tuple of (processed_html, result)
    """
    return get_pdf_guard().guard_and_process(html)


def is_pdf_content_allowed(html: str) -> bool:
    """
    Quick check if PDF content is allowed.

    Returns:
        True if content passes all checks
    """
    return get_pdf_guard().check(html).allowed


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info(
    "[G12] PDF Guard loaded - enabled=%s max_size=%.1fMB max_tables=%d max_images=%d fail=%s",
    PDF_GUARD_ENABLED,
    PDF_MAX_HTML_MB,
    PDF_MAX_TABLES,
    PDF_MAX_IMAGES,
    PDF_FAIL_ON_OVERSIZE,
)
