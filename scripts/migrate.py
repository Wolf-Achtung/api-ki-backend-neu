# -*- coding: utf-8 -*-
from __future__ import annotations
"""CLI‑Runner für Migrationen.
Verwendung: python -m scripts.migrate
"""
from core.db import engine
from core.migrate import migrate_all

if __name__ == "__main__":
    migrate_all(engine)
    print("Migrations done.")
