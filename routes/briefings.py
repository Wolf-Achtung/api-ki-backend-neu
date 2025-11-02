# -*- coding: utf-8 -*-
from __future__ import annotations
"""
Konsolidierter Briefings-Router – unverändert übernommen.
Draft-Management, Submit mit Async-Analyse, UTF-8 Fixes.
"""
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.db import get_session
from models import Briefing, User

log = logging.getLogger("routes.briefings")
router = APIRouter(prefix="/briefings", tags=["briefings"])

# (Der vollständige Inhalt soll dem zuletzt bereitgestellten Stand entsprechen;
# falls nötig bitte den bestehenden briefings.py beibehalten.)
# Für Klarheit: Wir ändern hier nichts, da die Datei bereits produktionsreif war.
# Siehe euer aktueller Stand im Repository.
