import os
import logging
import requests
from typing import Dict, Any, Optional

log = logging.getLogger(__name__)

PDF_SERVICE_URL = os.getenv("PDF_SERVICE_URL", "https://make-ki-pdfservice-production.up.railway.app")
PDF_TIMEOUT_MS = int(os.getenv("PDF_TIMEOUT_MS", "90000"))

def render_pdf_from_html(html: str, meta: Dict[str, Any]) -> Dict[str, Any]:
    """Ruft externen PDF-Service auf und gibt pdf_url oder pdf_bytes zurück."""
    
    if not PDF_SERVICE_URL:
        log.error("PDF_SERVICE_URL not configured!")
        return {"pdf_url": None, "pdf_bytes": None, "error": "PDF service not configured"}
    
    try:
        endpoint = f"{PDF_SERVICE_URL.rstrip('/')}/generate-pdf"
        
        payload = {
            "html": html,
            "filename": f"KI-Status-Report-{meta.get('briefing_id', 'report')}.pdf",
            "maxBytes": 15 * 1024 * 1024  # 15 MB
        }
        
        timeout_sec = PDF_TIMEOUT_MS / 1000
        log.info(f"Calling PDF service: {endpoint} (timeout={timeout_sec}s)")
        
        response = requests.post(
            endpoint,
            json=payload,
            timeout=timeout_sec,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "")
            
            if "application/pdf" in content_type:
                # PDF als Bytes zurück
                pdf_bytes = response.content
                log.info(f"PDF generated successfully: {len(pdf_bytes)} bytes")
                return {
                    "pdf_url": None,
                    "pdf_bytes": pdf_bytes,
                    "error": None
                }
            elif "application/json" in content_type:
                # JSON mit base64
                data = response.json()
                if data.get("ok") and "pdf_base64" in data:
                    import base64
                    pdf_bytes = base64.b64decode(data["pdf_base64"])
                    log.info(f"PDF generated (base64): {len(pdf_bytes)} bytes")
                    return {
                        "pdf_url": None,
                        "pdf_bytes": pdf_bytes,
                        "error": None
                    }
                else:
                    error = data.get("error", "Unknown error")
                    log.error(f"PDF service returned error: {error}")
                    return {"pdf_url": None, "pdf_bytes": None, "error": error}
        
        elif response.status_code == 413:
            log.error("PDF too large (413)")
            return {"pdf_url": None, "pdf_bytes": None, "error": "PDF exceeds size limit"}
        
        else:
            log.error(f"PDF service error: {response.status_code} - {response.text[:200]}")
            return {
                "pdf_url": None,
                "pdf_bytes": None,
                "error": f"HTTP {response.status_code}"
            }
    
    except requests.Timeout:
        log.error(f"PDF service timeout after {timeout_sec}s")
        return {"pdf_url": None, "pdf_bytes": None, "error": "Timeout"}
    
    except Exception as e:
        log.exception(f"PDF generation failed: {e}")
        return {"pdf_url": None, "pdf_bytes": None, "error": str(e)}
