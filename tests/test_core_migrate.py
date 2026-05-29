# -*- coding: utf-8 -*-
"""Tests for core.migrate (Sprint 1027.4 Item 1A).

Verifies that migrate_all iterates migrations/*.sql in addition to the
hardcoded DDL list and that the dialect-filter (sqlite vs. postgres) works.
"""
from __future__ import annotations

import os
import tempfile

import pytest
from sqlalchemy import create_engine, inspect, text

from core import migrate as core_migrate


def _write(folder: str, name: str, content: str) -> str:
    path = os.path.join(folder, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return path


def test_select_migration_files_filters_by_dialect(tmp_path):
    folder = str(tmp_path)
    _write(folder, "2025-01-01_a_postgres.sql", "-- pg\n")
    _write(folder, "2025-01-01_a_sqlite.sql", "-- sqlite\n")
    _write(folder, "2025-02-01_no_suffix.sql", "-- pg default\n")

    pg = core_migrate._select_migration_files("postgresql", migrations_dir=folder)
    sl = core_migrate._select_migration_files("sqlite", migrations_dir=folder)

    assert [os.path.basename(p) for p in pg] == [
        "2025-01-01_a_postgres.sql",
        "2025-02-01_no_suffix.sql",
    ]
    assert [os.path.basename(p) for p in sl] == ["2025-01-01_a_sqlite.sql"]


def test_select_migration_files_sorted_chronologically(tmp_path):
    folder = str(tmp_path)
    _write(folder, "2025-02-01_b.sql", "-- b\n")
    _write(folder, "2025-01-01_a.sql", "-- a\n")
    _write(folder, "2025-12-31_c.sql", "-- c\n")

    pg = core_migrate._select_migration_files("postgresql", migrations_dir=folder)
    assert [os.path.basename(p) for p in pg] == [
        "2025-01-01_a.sql",
        "2025-02-01_b.sql",
        "2025-12-31_c.sql",
    ]


def test_select_migration_files_missing_dir_returns_empty(tmp_path):
    missing = os.path.join(str(tmp_path), "does_not_exist")
    assert core_migrate._select_migration_files("postgresql", migrations_dir=missing) == []


def test_migrate_all_applies_sqlite_file_idempotently(tmp_path, monkeypatch):
    """End-to-end on an in-memory SQLite engine. Verifies the new file-iterator
    runs the *_sqlite.sql files, ignores *_postgres.sql, and is idempotent."""
    folder = str(tmp_path / "migrations")
    os.makedirs(folder)
    _write(
        folder,
        "2030-01-01_create_widgets_sqlite.sql",
        "CREATE TABLE IF NOT EXISTS widgets (id INTEGER PRIMARY KEY, name TEXT);\n"
        "CREATE INDEX IF NOT EXISTS idx_widgets_name ON widgets(name);\n",
    )
    _write(
        folder,
        "2030-01-02_add_color_sqlite.sql",
        "ALTER TABLE widgets ADD COLUMN color TEXT;\n",
    )
    # Postgres-only file must be ignored on SQLite:
    _write(
        folder,
        "2030-01-03_pg_only_postgres.sql",
        "ALTER TABLE widgets ADD COLUMN jsonb_thing JSONB;\n",
    )

    monkeypatch.setattr(core_migrate, "MIGRATIONS_DIR", folder)
    # Don't run the hardcoded Postgres DDL list on SQLite — it uses TIMESTAMPTZ/JSONB/SERIAL.
    monkeypatch.setattr(core_migrate, "DDL", [])

    engine = create_engine("sqlite:///:memory:")

    # First run: applies both sqlite files, skips the postgres one.
    core_migrate.migrate_all(engine)
    cols = {c["name"] for c in inspect(engine).get_columns("widgets")}
    assert cols == {"id", "name", "color"}, cols

    # Second run: ADD COLUMN is not natively idempotent on SQLite — our
    # graceful handler must swallow the "duplicate column" error.
    core_migrate.migrate_all(engine)
    cols = {c["name"] for c in inspect(engine).get_columns("widgets")}
    assert cols == {"id", "name", "color"}, cols
