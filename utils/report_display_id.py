"""Unified customer-facing report number (KIS-XXXX) for all three report types."""

import os


def get_report_display_id(briefing_id: int) -> str:
    """Compute the customer-friendly report number.

    Uses ENV ``REPORT_DISPLAY_OFFSET`` (default 0) so that e.g.
    briefing 883 + offset 117 → KIS-1000.
    """
    offset = int(os.getenv("REPORT_DISPLAY_OFFSET", "0"))
    display_number = briefing_id + offset
    return f"KIS-{display_number:04d}"
