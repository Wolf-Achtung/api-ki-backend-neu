# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

from gpt_analyze import run_async

router = APIRouter(prefix="/api/report", tags=["report"])

class ReportPayload(BaseModel):
  lang: str = "de"
  answers: Dict[str, Any]

def _jinja_env(template_dir: str | Path):
  env = Environment(
    loader=FileSystemLoader(str(template_dir)),
    autoescape=select_autoescape(enabled_extensions=("html","xml"))
  )
  return env

@router.get("/ping")
def ping()->Dict[str,str]:
  return {"status":"ok"}

@router.post("/render")
def render_html(payload: ReportPayload):
  try:
    vars = run_async(payload.dict())
    template_dir = Path("templates")
    tpl_name = "pdf_template.html"
    env = _jinja_env(template_dir)
    tpl = env.get_template(tpl_name)
    html = tpl.render(**vars)
    return {"html": html, "vars": vars}
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"render failed: {e}")
