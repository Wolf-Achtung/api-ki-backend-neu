#!/usr/bin/env python3
"""
RUN-622 Code-Patches: P1 + P2 + P5
===================================
P1: Token-Budget Diagnostik-Logging in _llm_params_for()
P2: Opus Routing für 5 Premium-Sections in anthropic_client.py
P5: TBD/TODO/N/A Filter in _clean_html()

Ausführen im Repo-Root:
    python3 PATCH-CODE-RUN622.py
"""

import os
import sys
import shutil
from pathlib import Path


def find_file(name: str) -> Path:
    """Find file in workspace."""
    for root, dirs, files in os.walk("/workspaces"):
        dirs[:] = [d for d in dirs if d not in ("node_modules", ".git", "__pycache__")]
        if name in files and "backup" not in root and "bak" not in root:
            return Path(root) / name
    # Fallback: current dir
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in ("node_modules", ".git", "__pycache__")]
        if name in files and "backup" not in root:
            return Path(root) / name
    return None


def patch_file(filepath: Path, old: str, new: str, label: str) -> bool:
    """Replace old with new in file. Returns True on success."""
    content = filepath.read_text(encoding="utf-8")
    if old not in content:
        print(f"   ❌ {label}: Patch-Stelle nicht gefunden! Bereits gepatcht?")
        # Check if new content already exists
        if new in content or label.split(":")[0].strip() in content:
            print(f"   ℹ️  Sieht aus als wäre {label} bereits applied.")
            return True
        return False
    content = content.replace(old, new, 1)
    filepath.write_text(content, encoding="utf-8")
    print(f"   ✅ {label}")
    return True


def main():
    print("=" * 64)
    print("  CODE-PATCHES RUN-622: P1 + P2 + P5")
    print("=" * 64)
    print()

    # Find files
    gpt_file = find_file("gpt_analyze.py")
    anthro_file = find_file("anthropic_client.py")

    if not gpt_file:
        print("❌ gpt_analyze.py nicht gefunden!")
        sys.exit(1)
    if not anthro_file:
        print("❌ anthropic_client.py nicht gefunden!")
        sys.exit(1)

    print(f"📂 gpt_analyze.py:      {gpt_file}")
    print(f"📂 anthropic_client.py:  {anthro_file}")
    print()

    # Backup
    print("📦 Backup erstellen...")
    shutil.copy2(gpt_file, str(gpt_file) + ".bak_run622")
    shutil.copy2(anthro_file, str(anthro_file) + ".bak_run622")
    print("   ✅ Backups erstellt")
    print()

    ok = True

    # ==================================================================
    # P2a: Opus Routing Konstanten
    # ==================================================================
    print("🔧 P2a: Opus Routing Konstanten...")
    ok &= patch_file(
        anthro_file,
        old=(
            'DEFAULT_TEMPERATURE = float(os.getenv("ANTHROPIC_TEMPERATURE", "0.2"))\n'
            '\n'
            '# z.B. USE_ANTHROPIC_FOR_EXEC_SUMMARY, USE_ANTHROPIC_FOR_RISKS, ...\n'
            'SECTION_FLAG_PREFIX = "USE_ANTHROPIC_FOR_"'
        ),
        new=(
            'DEFAULT_TEMPERATURE = float(os.getenv("ANTHROPIC_TEMPERATURE", "0.2"))\n'
            '\n'
            '# --- RUN-622 P2: Opus Routing ------------------------------------------------\n'
            'OPUS_MODEL = os.getenv("ANTHROPIC_MODEL_OPUS", "claude-opus-4-5-20250929")\n'
            '_OPUS_SECTIONS_RAW = os.getenv("OPUS_SECTIONS", "")\n'
            'OPUS_SECTIONS_SET: set = {\n'
            '    s.strip().lower()\n'
            '    for s in _OPUS_SECTIONS_RAW.split(",")\n'
            '    if s.strip()\n'
            '}\n'
            'if OPUS_SECTIONS_SET:\n'
            '    log.info(\n'
            '        "🎯 [RUN-622] Opus routing enabled for %d sections: %s",\n'
            '        len(OPUS_SECTIONS_SET), sorted(OPUS_SECTIONS_SET),\n'
            '    )\n'
            'else:\n'
            '    log.info("ℹ️ [RUN-622] Opus routing disabled (OPUS_SECTIONS not set)")\n'
            '\n'
            '# z.B. USE_ANTHROPIC_FOR_EXEC_SUMMARY, USE_ANTHROPIC_FOR_RISKS, ...\n'
            'SECTION_FLAG_PREFIX = "USE_ANTHROPIC_FOR_"'
        ),
        label="P2a: Opus Konstanten",
    )

    # ==================================================================
    # P2b: Opus Routing Logic in _resolve_anthropic_model()
    # ==================================================================
    print("🔧 P2b: Opus Routing Logic...")
    ok &= patch_file(
        anthro_file,
        old=(
            '            return section_model\n'
            '    \n'
            '    # 2. Globale ENV-Variablen\n'
            '    global_model = os.getenv("ANTHROPIC_MODEL_DEFAULT") or os.getenv("ANTHROPIC_MODEL")'
        ),
        new=(
            '            return section_model\n'
            '    \n'
            '    # 1b. RUN-622 P2: Opus Routing via OPUS_SECTIONS ENV\n'
            '    section_lower = (section or "").strip().lower()\n'
            '    if section_lower in OPUS_SECTIONS_SET:\n'
            '        log.info(\n'
            '            "🎯 anthropic_client: Opus routing → \'%s\' for section \'%s\' (source=\'OPUS_SECTIONS\')",\n'
            '            OPUS_MODEL, section,\n'
            '        )\n'
            '        return OPUS_MODEL\n'
            '    \n'
            '    # 2. Globale ENV-Variablen\n'
            '    global_model = os.getenv("ANTHROPIC_MODEL_DEFAULT") or os.getenv("ANTHROPIC_MODEL")'
        ),
        label="P2b: Opus Routing Logic",
    )

    # ==================================================================
    # P1: Token-Budget Diagnostik-Logging
    # ==================================================================
    print("🔧 P1: Token-Budget Diagnostik-Logging...")
    ok &= patch_file(
        gpt_file,
        old=(
            '    else:\n'
            '        max_tokens = OPENAI_MAX_TOKENS_DEFAULT\n'
            '\n'
            '    return {\n'
            '        "model": model,\n'
            '        "temperature": temperature,\n'
            '        "max_tokens": max_tokens,\n'
            '        "timeout": OPENAI_TIMEOUT_SEC,\n'
            '    }\n'
            '\n'
            '# ========================================================================\n'
            '\n'
            'def build_extra_sections(answers: dict, scores: dict) -> dict:'
        ),
        new=(
            '    else:\n'
            '        max_tokens = OPENAI_MAX_TOKENS_DEFAULT\n'
            '\n'
            '    # === RUN-622 P1: Diagnostik-Logging für Token-Budget-Auflösung ===\n'
            '    _token_source = "ENV" if max_tokens_env is not None else (\n'
            '        "_SECTION_MAX_TOKENS" if key in _SECTION_MAX_TOKENS else (\n'
            '            "platin_config" if platin_config else "global_default"\n'
            '        )\n'
            '    )\n'
            '    log.info(\n'
            '        "[TokenBudget] section=%s → max_tokens=%d (source=%s, model=%s)",\n'
            '        section_key, max_tokens, _token_source, model\n'
            '    )\n'
            '\n'
            '    return {\n'
            '        "model": model,\n'
            '        "temperature": temperature,\n'
            '        "max_tokens": max_tokens,\n'
            '        "timeout": OPENAI_TIMEOUT_SEC,\n'
            '    }\n'
            '\n'
            '# ========================================================================\n'
            '\n'
            'def build_extra_sections(answers: dict, scores: dict) -> dict:'
        ),
        label="P1: Token-Budget Logging",
    )

    # ==================================================================
    # P5: TBD/TODO/N/A Filter in _clean_html()
    # ==================================================================
    print("🔧 P5: TBD/TODO Filter...")
    ok &= patch_file(
        gpt_file,
        old=(
            "        r'(?i)Wenn\\s+Sie\\s+magst,?\\s*strong>[^.]*',\n"
            "    ]"
        ),
        new=(
            "        r'(?i)Wenn\\s+Sie\\s+magst,?\\s*strong>[^.]*',\n"
            "        # RUN-622 P5: TBD/TODO/N/A Placeholder-Filter\n"
            "        r'(?i)\\bTBD\\b',\n"
            "        r'(?i)\\bTODO\\b',\n"
            "        r'(?i)\\b(?:N/A|n/a)\\b',\n"
            "        r'\\[(?:hier ergänzen|to be defined|noch offen|\\.\\.\\.)\\]',\n"
            "    ]"
        ),
        label="P5: TBD/TODO Filter",
    )

    # ==================================================================
    # VALIDIERUNG
    # ==================================================================
    print()
    print("=" * 64)
    print("  VALIDIERUNG")
    print("=" * 64)

    anthro_content = anthro_file.read_text()
    gpt_content = gpt_file.read_text()

    checks = [
        ("P2 Opus Konstanten", "OPUS_SECTIONS_SET" in anthro_content),
        ("P2 Opus Routing",    "Opus routing →" in anthro_content or "Opus routing" in anthro_content),
        ("P1 Token Logging",   "[TokenBudget]" in gpt_content),
        ("P5 TBD Filter",      "RUN-622 P5" in gpt_content),
    ]

    for label, passed in checks:
        icon = "✅" if passed else "❌"
        print(f"  {icon} {label}")

    all_ok = all(p for _, p in checks)
    print()

    if all_ok:
        print("=" * 64)
        print("  ✅ ALLE 3 PATCHES ERFOLGREICH!")
        print("=" * 64)
    else:
        print("=" * 64)
        print("  ⚠️  NICHT ALLE PATCHES APPLIED — siehe oben")
        print("=" * 64)

    print()
    print("  NÄCHSTE SCHRITTE:")
    print()
    print("  1. Git commit:")
    print('     git add -A')
    print('     git commit -m "RUN-622: P1+P2+P5 Code-Patches (Token-Logging, Opus-Routing, TBD-Filter)"')
    print('     git push')
    print()
    print("  2. Railway ENVs setzen (Settings → Variables):")
    print("     OPUS_SECTIONS=executive_summary,business_case,gamechanger,roadmap_12m,branch_deep_dive")
    print("     ANTHROPIC_MODEL_OPUS=claude-opus-4-5-20250929")
    print()
    print("  3. Test-Run starten und Logs prüfen:")
    print("     grep 'TokenBudget' <railway-logs>")
    print("     grep 'Opus routing' <railway-logs>")
    print()
    print(f"  ROLLBACK:")
    print(f"     cp {gpt_file}.bak_run622 {gpt_file}")
    print(f"     cp {anthro_file}.bak_run622 {anthro_file}")
    print("=" * 64)


if __name__ == "__main__":
    main()
