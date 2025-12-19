# Report Frontmatter Documentation

This document describes the metadata and presentation elements used in PDF reports.

## PDF Footer

Every page of the generated PDF report includes a footer with the following information:

### Left Side
- **Page Numbers**: `Seite X / Y` (Page X of Y)

### Right Side
- **Report ID**: Unique identifier in format `R-YYYYMMDD-CODE` (e.g., `R-20251219-KND`)
- **Report Date**: Date in German format `DD.MM.YYYY` (e.g., `19.12.2025`)

### Example Footer
```
Seite 1 / 15                                    Report-ID: R-20251219-KND • 19.12.2025
```

## Technical Implementation

### Footer Template (Puppeteer)
The footer is rendered using Puppeteer's `displayHeaderFooter` option with a custom `footerTemplate`:

```python
from services.pdf_client import build_footer_template

footer_template = build_footer_template(
    report_id="R-20251219-KND",
    report_date="19.12.2025"
)

pdf_options = {
    "format": "A4",
    "printBackground": True,
    "displayHeaderFooter": True,
    "headerTemplate": "<div></div>",
    "footerTemplate": footer_template,
    "margin": {"top": "12mm", "right": "12mm", "bottom": "20mm", "left": "12mm"}
}
```

### Data Sources
- **report_id**: Generated from `R-{YYYYMMDD}-{customer_code}` during report analysis
- **report_date**: Current date in `DD.MM.YYYY` format, set during report generation

### Fallback Behavior
If `report_id` or `report_date` are not available:
- Missing values are replaced with `–` (en-dash)
- The footer will still display page numbers correctly

### Margin Configuration
- **Bottom margin**: 20mm to accommodate the footer without overlapping content
- **Top margin**: 12mm
- **Left/Right margins**: 12mm

## Related Files

- `services/pdf_client.py` - Contains `build_footer_template()` and `render_pdf_from_html()`
- `services/report_renderer.py` - Extracts report metadata for footer
- `gpt_analyze.py` - Main report generation pipeline
- `routes/report.py` - On-demand PDF generation endpoint
