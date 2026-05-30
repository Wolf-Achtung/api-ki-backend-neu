# -*- coding: utf-8 -*-
"""FIX-KIS-1027.5-D: mise.toml im Repo-Root.

Sprint 1027.4 hatte einen mise-Tooling-Build-Fehler:
"No GitHub artifact attestations found for python@3.11.9"
gefixt mit MISE_PYTHON_GITHUB_ATTESTATIONS=false im Railway-Dashboard.
Dashboard-ENV-Var ist nicht repo-controlled — bei mise-Default-Wechsel
oder Service-Migration bricht es wieder.

Fix: mise.toml im Repo-Root mit pinned Python-Version und expliziter
attestations-Deaktivierung.
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).parent.parent
MISE_TOML = ROOT / "mise.toml"


def test_mise_toml_exists():
    """mise.toml liegt im Repo-Root."""
    assert MISE_TOML.exists(), (
        "mise.toml fehlt im Repo-Root. Build wird bei "
        "mise-Default-Aenderung brechen."
    )


def test_mise_toml_pins_python_version():
    """Python-Version explizit gepinnt (deterministischer Build)."""
    content = MISE_TOML.read_text(encoding="utf-8")
    assert "python" in content.lower(), "Python-Pinning fehlt in mise.toml"
    # Mindestens eine konkrete Version (z. B. 3.11.x)
    import re
    assert re.search(r'python\s*=\s*"3\.\d+', content), (
        "Python-Version nicht semver-format gepinnt"
    )


def test_mise_toml_disables_python_github_attestations():
    """python_github_attestations = false (Railway-Build-Fix)."""
    content = MISE_TOML.read_text(encoding="utf-8")
    assert "python_github_attestations" in content, (
        "python_github_attestations Setting fehlt in mise.toml"
    )
    assert "false" in content.lower(), (
        "python_github_attestations nicht auf false gesetzt"
    )
