# -*- coding: utf-8 -*-
from __future__ import annotations
import io
import json
import logging
from typing import Optional

from sqlalchemy.orm import Session
from zipfile import ZipFile, ZIP_DEFLATED

from models import Briefing, Analysis, Report

log = logging.getLogger(__name__)


def build_briefing_export_zip(db: Session, briefing_id: int, include_pdf: bool = False) -> Optional[io.BytesIO]:
    b = db.get(Briefing, briefing_id)
    if not b:
        return None
    a = db.query(Analysis).filter(Analysis.briefing_id == briefing_id).order_by(Analysis.id.desc()).first()
    r = db.query(Report).filter(Report.briefing_id == briefing_id).order_by(Report.id.desc()).first()

    mem = io.BytesIO()
    with ZipFile(mem, "w", ZIP_DEFLATED) as z:
        z.writestr("briefing.json", json.dumps({
            "id": b.id,
            "user_id": b.user_id,
            "lang": getattr(b, "lang", "de"),
            "answers": getattr(b, "answers", {}),
            "created_at": getattr(b, "created_at", None).isoformat() if getattr(b, "created_at", None) else None,
        }, ensure_ascii=False, indent=2))

        if a:
            z.writestr("analysis/meta.json", json.dumps(getattr(a, "meta", {}) or {}, ensure_ascii=False, indent=2))
            z.writestr("analysis/report.html", getattr(a, "html", "") or "")

        if r:
            z.writestr("report/info.json", json.dumps({
                "id": r.id,
                "pdf_url": getattr(r, "pdf_url", None),
                "pdf_bytes_len": getattr(r, "pdf_bytes_len", None),
                "created_at": getattr(r, "created_at", None).isoformat() if getattr(r, "created_at", None) else None,
            }, ensure_ascii=False, indent=2))
            if include_pdf and getattr(r, "pdf_bytes_len", None) and hasattr(r, "pdf_bytes"):
                # Falls euer Modell pdf_bytes als LargeBinary hält
                try:
                    z.writestr("report/report.pdf", getattr(r, "pdf_bytes"))
                except Exception:
                    log.warning("report.pdf_bytes not accessible / skipped.")

    mem.seek(0)
    return mem
