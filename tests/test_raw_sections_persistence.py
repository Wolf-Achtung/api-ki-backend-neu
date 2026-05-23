"""Sprint 1027.3 / Item H: Source-level guard für Pre-/Post-Healer-
Section-Snapshot-Persistence in R1.

Prüft direkt am Source (analog test_decision_section_figure_wrapper.py),
ohne einen vollen analyze_briefing()-Run zu fahren (würde LLM-Calls,
DB-Setup, Briefing-Fixture etc. erfordern).

Coverage:
- Migration-Files für Postgres + SQLite existieren mit erwartetem DDL.
- Analysis-Model hat raw_sections-Spalte (Mapped[Optional[dict]]).
- gpt_analyze.analyze_briefing hat die drei Hooks (Init, Pre-Snapshot,
  Post-Snapshot, DB-Write).
"""
from __future__ import annotations

import os
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GPT_ANALYZE = os.path.join(REPO_ROOT, "gpt_analyze.py")
MODELS = os.path.join(REPO_ROOT, "models.py")
MIG_PG = os.path.join(
    REPO_ROOT, "migrations", "2026-05-22_add_analyses_raw_sections_postgres.sql"
)
MIG_SQ = os.path.join(
    REPO_ROOT, "migrations", "2026-05-22_add_analyses_raw_sections_sqlite.sql"
)


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestMigrationFiles:
    def test_postgres_migration_exists_with_jsonb_and_gin(self) -> None:
        assert os.path.exists(MIG_PG), f"missing migration: {MIG_PG}"
        sql = _read(MIG_PG)
        assert re.search(
            r"ALTER\s+TABLE\s+analyses\s+ADD\s+COLUMN\s+IF\s+NOT\s+EXISTS\s+raw_sections\s+JSONB",
            sql,
            re.IGNORECASE,
        ), "Postgres-Migration fehlt JSONB-Spaltendefinition"
        assert re.search(
            r"CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_analyses_raw_sections_gin\s+ON\s+analyses\s+USING\s+GIN\s*\(\s*raw_sections\s*\)",
            sql,
            re.IGNORECASE,
        ), "Postgres-Migration fehlt GIN-Index"

    def test_sqlite_migration_exists_with_json_column(self) -> None:
        assert os.path.exists(MIG_SQ), f"missing migration: {MIG_SQ}"
        sql = _read(MIG_SQ)
        assert re.search(
            r"ALTER\s+TABLE\s+analyses\s+ADD\s+COLUMN\s+raw_sections\s+JSON",
            sql,
            re.IGNORECASE,
        ), "SQLite-Migration fehlt JSON-Spaltendefinition"
        # SQLite hat kein GIN — sicherstellen dass kein versehentlich
        # mitgewanderter GIN-Index in einem DDL-Statement steht
        # (Kommentare mit dem Wort "GIN" sind erlaubt — die Erklärung
        # WARUM kein GIN-Index gehört in die SQLite-Variant-Doku).
        sql_no_comments = re.sub(r"--[^\n]*", "", sql)
        assert not re.search(
            r"\bUSING\s+GIN\b|\bGIN\s*\(", sql_no_comments, re.IGNORECASE
        ), "SQLite-Migration enthält GIN-Index-DDL — SQLite kennt keine GIN-Indizes"


class TestAnalysisModelColumn:
    def test_analysis_has_raw_sections_column(self) -> None:
        os.environ.setdefault("JWT_SECRET", "test-only-for-model-import")
        os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
        from models import Analysis

        columns = [c.name for c in Analysis.__table__.columns]
        assert "raw_sections" in columns, (
            f"Analysis-Model fehlt raw_sections-Spalte. cols={columns}"
        )
        # Spalte muss nullable sein (NULL für vor-1027.3 Rows)
        col = Analysis.__table__.columns["raw_sections"]
        assert col.nullable is True, (
            "raw_sections muss nullable sein (Backfill-Konvention)"
        )


class TestPipelineHooks:
    def test_pre_healer_snapshot_hook_present(self) -> None:
        src = _read(GPT_ANALYZE)
        # Init der beiden Vars (vor Healer-try-Block)
        assert re.search(
            r"_raw_pre_healer_sections\s*:\s*Optional\[Dict\[str,\s*str\]\]\s*=\s*None",
            src,
        ), "Pre-Healer-Var-Init fehlt"
        assert re.search(
            r"_raw_post_healer_sections\s*:\s*Optional\[Dict\[str,\s*str\]\]\s*=\s*None",
            src,
        ), "Post-Healer-Var-Init fehlt"
        # Pre-Snapshot-Assignment via dict-comprehension (String-Filter)
        pre_snap = re.search(
            r"_raw_pre_healer_sections\s*=\s*\{\s*k\s*:\s*v\s+for\s+k,\s*v\s+in\s+sections\.items\(\)\s+if\s+isinstance\(v,\s*str\)",
            src,
        )
        assert pre_snap, "Pre-Healer-Snapshot-Comprehension fehlt"

    def test_post_healer_snapshot_hook_present(self) -> None:
        src = _read(GPT_ANALYZE)
        # Post-Snapshot direkt nach `sections = healing_result.sections`
        m = re.search(
            r"sections\s*=\s*healing_result\.sections.*?_raw_post_healer_sections\s*=\s*\{\s*k\s*:\s*v\s+for\s+k,\s*v\s+in\s+sections\.items\(\)\s+if\s+isinstance\(v,\s*str\)",
            src,
            re.DOTALL,
        )
        assert m, (
            "Post-Healer-Snapshot fehlt oder steht nicht direkt nach "
            "`sections = healing_result.sections`"
        )

    def test_post_healer_snapshot_runs_before_healer_stats(self) -> None:
        """Snapshot muss VOR _healer_stats-Injection laufen, sonst
        landet das Stats-Meta-Key versehentlich im Snapshot."""
        src = _read(GPT_ANALYZE)
        m_snap = re.search(
            r"_raw_post_healer_sections\s*=\s*_copy_rs\.deepcopy",
            src,
        )
        m_stats = re.search(
            r'sections\[\s*"_healer_stats"\s*\]\s*=\s*_json_healer\.dumps',
            src,
        )
        assert m_snap and m_stats, "Snapshot- oder Stats-Marker fehlt"
        assert m_snap.start() < m_stats.start(), (
            "Post-Healer-Snapshot läuft NACH _healer_stats-Injection — "
            "Stats würden im Snapshot landen, Reihenfolge umdrehen."
        )

    def test_db_write_hook_present_after_analysis_refresh(self) -> None:
        src = _read(GPT_ANALYZE)
        # DB-Write: nach db.refresh(an), nutzt an.raw_sections + db.commit().
        m = re.search(
            r"db\.refresh\(an\).*?an\.raw_sections\s*=\s*\{.*?\"pre_healer\".*?\"post_healer\".*?\}.*?db\.commit\(\)",
            src,
            re.DOTALL,
        )
        assert m, (
            "DB-Write-Hook fehlt — erwarte nach db.refresh(an) einen "
            "an.raw_sections-Assignment mit pre_healer/post_healer-Keys "
            "gefolgt von db.commit()."
        )

    def test_db_write_hook_is_non_blocking(self) -> None:
        """Schreibfehler dürfen nicht raisen (Pipeline läuft durch)."""
        src = _read(GPT_ANALYZE)
        # Hook muss in try/except gewrappt sein, mit log.warning, nicht raise.
        m = re.search(
            r"try:\s*\n\s*if\s+_raw_pre_healer_sections\s+is\s+not\s+None\s+or\s+_raw_post_healer_sections\s+is\s+not\s+None.*?except\s+Exception\s+as\s+_rs_err.*?log\.warning",
            src,
            re.DOTALL,
        )
        assert m, (
            "DB-Write-Hook ist nicht non-blocking — erwarte try/except + "
            "log.warning, nie raise"
        )


class TestSnapshotIsTrueCopy:
    """Functional Test: Pre- und Post-Healer-Snapshots sind echte
    Trennung, nicht zweimal dasselbe Objekt.

    Methodik: Reproduziert die EXAKTE Snapshot-Logik aus
    gpt_analyze.py:20340-20347 + :20371-20381 gegen ein fixiertes
    sections-Dict mit zwei Sections:
      - Mutated:  enthält "<p></p>" — Fix-A in heal_report_html
        (sanitize_template_phrases Z.874) entfernt empty-paragraphs
        unbedingt → garantierte Mutation.
      - Control: neutraler HTML-Text ohne Trigger-Pattern → vom
        Healer nicht mutiert.

    Assertion-Kern:
      - pre[mutated]  !=  post[mutated]   (echte Trennung)
      - pre[control]  ==  post[control]   (Snapshot stabil)
      - pre[mutated]  enthält noch "<p></p>" (Pre unverändert)
      - post[mutated] enthält "<p></p>" nicht mehr (Healer hat gewirkt)

    Wenn die Snapshot-Logik versehentlich auf eine Reference statt
    Comprehension-Copy umgestellt würde, würden pre und post auf
    dasselbe (geheilte) Dict zeigen und die erste Assertion failed.
    """

    def test_pre_post_are_independent_objects(self) -> None:
        os.environ.setdefault("JWT_SECRET", "test-only")
        os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

        import copy

        from services.report_healer import heal_report_html

        sections = {
            "EXECUTIVE_DECISION_HTML": (
                "<p>Realer Inhalt vor dem Cleanup.</p>"
                "<p></p>"
                "<p>Realer Inhalt danach.</p>"
            ),
            "EXECUTIVE_SUMMARY_HTML": "<p>Ein neutraler Hinweis.</p>",
        }

        # === Snapshot Pre-Healer (identisch zu gpt_analyze.py:20340-20347) ===
        pre = {
            k: v for k, v in sections.items()
            if isinstance(v, str) and not k.startswith("_")
        }
        pre = copy.deepcopy(pre)

        # === Run real healer ===
        result = heal_report_html(sections, segment="solo")
        healed = result.sections

        # === Snapshot Post-Healer (identisch zu gpt_analyze.py:20371-20381) ===
        post = {
            k: v for k, v in healed.items()
            if isinstance(v, str) and not k.startswith("_")
        }
        post = copy.deepcopy(post)

        # === Assertions ===
        # 1. Mutated section: pre != post (echte Trennung)
        assert pre["EXECUTIVE_DECISION_HTML"] != post["EXECUTIVE_DECISION_HTML"], (
            "Pre und Post sind IDENTISCH für EXECUTIVE_DECISION_HTML — "
            "Snapshot ist vermutlich Reference statt Copy, oder Healer hat "
            "die erwartete Fix-A-Mutation nicht durchgeführt.\n"
            f"  pre={pre['EXECUTIVE_DECISION_HTML']!r}\n"
            f"  post={post['EXECUTIVE_DECISION_HTML']!r}"
        )

        # 2. Pre ist unverändert (enthält noch das Trigger-Pattern)
        assert "<p></p>" in pre["EXECUTIVE_DECISION_HTML"], (
            "Pre-Snapshot wurde nach-mutiert — Reference-Bug? "
            f"pre={pre['EXECUTIVE_DECISION_HTML']!r}"
        )

        # 3. Post ist sauber (Healer hat <p></p> entfernt)
        assert "<p></p>" not in post["EXECUTIVE_DECISION_HTML"], (
            "Post-Snapshot enthält noch <p></p> — Fix-A hat nicht gegriffen, "
            "Healer-Annahme falsch (Test-Fixture muss aktualisiert werden)."
            f" post={post['EXECUTIVE_DECISION_HTML']!r}"
        )

        # 4. Control section: pre == post (Snapshot stabil, kein False-Positive)
        assert pre["EXECUTIVE_SUMMARY_HTML"] == post["EXECUTIVE_SUMMARY_HTML"], (
            "Control-Section wurde unerwartet mutiert — entweder hat der "
            "Healer einen unerwarteten Fix angewendet, oder Pre-Snapshot "
            "ist eine Reference.\n"
            f"  pre={pre['EXECUTIVE_SUMMARY_HTML']!r}\n"
            f"  post={post['EXECUTIVE_SUMMARY_HTML']!r}"
        )
