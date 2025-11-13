# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Dict, Any
from datetime import datetime, timezone
from .research_clients import get_tools_for, tools_table_html, load_funding_programs, funding_table_html  # type: ignore

def run_research(answers: Dict[str, Any]) -> Dict[str, Any]:
    tools = get_tools_for(answers)
    programs = load_funding_programs()
    return {
        "TOOLS_TABLE_HTML": tools_table_html(tools),
        "FUNDING_TABLE_HTML": funding_table_html(programs),
        "last_updated": datetime.now(timezone.utc).strftime("%d.%m.%Y"),
    }
