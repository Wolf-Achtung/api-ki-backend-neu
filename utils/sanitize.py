# -*- coding: utf-8 -*-
import unicodedata

def ensure_utf8(text: str) -> str:
    if text is None:
        return ""
    if isinstance(text, bytes):
        try:
            return text.decode("utf-8", errors="replace")
        except Exception:
            return text.decode("latin-1", errors="replace")
    # Normalize to NFC to avoid accent issues
    return unicodedata.normalize("NFC", str(text))
