# -*- coding: utf-8 -*-
"""
routes/content.py — News research pipeline endpoint.

Provides a cron-triggered endpoint that researches current news
via Tavily, summarizes them via GPT-4o, and emails an HTML draft
to the admin for editorial review.
"""
from __future__ import annotations

import logging
import os

from fastapi import APIRouter, Header, HTTPException

from services.news_researcher import run_news_pipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/content", tags=["content"])

CRON_SECRET = os.getenv("CRON_SECRET", "")


@router.post("/research-news")
async def research_news_endpoint(
    x_cron_secret: str = Header(None, alias="X-Cron-Secret"),
):
    """
    Recherchiert aktuelle News und sendet Draft per E-Mail.

    Aufruf: Manuell oder via Cron-Job (Railway Cron oder externe Cron).
    Auth: X-Cron-Secret Header muss CRON_SECRET matchen.
    """
    if not CRON_SECRET or x_cron_secret != CRON_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        result = await run_news_pipeline()
        return result
    except Exception as e:
        logger.error("[NEWS] Research pipeline failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
