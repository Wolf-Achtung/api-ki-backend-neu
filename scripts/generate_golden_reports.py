#!/usr/bin/env python3
"""
generate_golden_reports.py – PLATIN+++ Golden Report Generator

Generiert Golden Report Artifacts für Release-Profile und fixiert sie mit SHA-256 Hashes.

WICHTIG: Dieses Skript erzeugt EINMALIG Golden Reports als Referenzartefakte.
Golden Reports dürfen NICHT automatisch überschrieben werden.

Ablauf:
1. Lädt Release-Profile aus data/release_profiles/
2. Generiert HTML und PDF Reports via API
3. Speichert Artifacts in artifacts/golden_reports/{solo,team,kmu}/
4. Berechnet SHA-256 Hashes und speichert sie in golden_manifest.json

CLI-Beispiele:
  # Alle Golden Reports generieren (erfordert --force wenn bereits vorhanden):
  python scripts/generate_golden_reports.py --base-url <URL> --email <EMAIL>

  # Nur Hash-Manifest aktualisieren (ohne neue Reports zu generieren):
  python scripts/generate_golden_reports.py --hash-only

  # Überschreiben von existierenden Golden Reports erzwingen:
  python scripts/generate_golden_reports.py --base-url <URL> --email <EMAIL> --force

Version: 1.0.0 (PLATIN+++ Release-Readiness)
"""

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import requests
except ImportError:
    requests = None  # type: ignore

# Repo-Root berechnen
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

# Pfade
RELEASE_PROFILES_DIR = REPO_ROOT / "data" / "release_profiles"
GOLDEN_REPORTS_DIR = REPO_ROOT / "artifacts" / "golden_reports"
GOLDEN_MANIFEST_PATH = GOLDEN_REPORTS_DIR / "golden_manifest.json"

# Profile
RELEASE_PROFILES = ["solo", "team", "kmu"]


def compute_sha256(file_path: Path) -> str:
    """Berechnet SHA-256 Hash einer Datei."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def load_release_profile(profile_type: str) -> Optional[Dict[str, Any]]:
    """Lädt ein Release-Profil aus data/release_profiles/."""
    profile_path = RELEASE_PROFILES_DIR / profile_type / "profile.json"
    if not profile_path.exists():
        print(f"  [ERROR] Release-Profil nicht gefunden: {profile_path}")
        return None

    try:
        with open(profile_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"  [ERROR] JSON Parse Error in {profile_path}: {e}")
        return None


def load_golden_manifest() -> Dict[str, Any]:
    """Lädt das Golden Manifest (oder erstellt ein leeres)."""
    if GOLDEN_MANIFEST_PATH.exists():
        try:
            with open(GOLDEN_MANIFEST_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass

    return {
        "_manifest_metadata": {
            "manifest_version": "1.0.0",
            "created_date": datetime.now().isoformat()[:10],
            "last_updated": datetime.now().isoformat()[:10],
            "purpose": "SHA-256 Hashes der Golden Report Artifacts",
            "checksum_algorithm": "SHA-256"
        },
        "artifacts": {}
    }


def save_golden_manifest(manifest: Dict[str, Any]) -> None:
    """Speichert das Golden Manifest."""
    manifest["_manifest_metadata"]["last_updated"] = datetime.now().isoformat()[:10]

    with open(GOLDEN_MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"  [OK] Golden Manifest gespeichert: {GOLDEN_MANIFEST_PATH}")


def check_existing_artifacts(profile_type: str) -> Dict[str, Path]:
    """Prüft auf existierende Golden Report Artifacts."""
    profile_dir = GOLDEN_REPORTS_DIR / profile_type
    existing = {}

    html_path = profile_dir / f"golden_report_{profile_type}.html"
    pdf_path = profile_dir / f"golden_report_{profile_type}.pdf"

    if html_path.exists():
        existing["html"] = html_path
    if pdf_path.exists():
        existing["pdf"] = pdf_path

    return existing


def update_hashes_only() -> bool:
    """Aktualisiert nur die Hashes im Manifest für existierende Artifacts."""
    print("\n" + "=" * 78)
    print("HASH-ONLY MODUS: Aktualisiere Hashes für existierende Artifacts")
    print("=" * 78)

    manifest = load_golden_manifest()
    updated_count = 0

    for profile_type in RELEASE_PROFILES:
        existing = check_existing_artifacts(profile_type)
        if not existing:
            print(f"\n[{profile_type}] Keine Artifacts gefunden - überspringe")
            continue

        print(f"\n[{profile_type}] Aktualisiere Hashes...")

        if profile_type not in manifest["artifacts"]:
            manifest["artifacts"][profile_type] = {}

        for artifact_type, artifact_path in existing.items():
            hash_value = compute_sha256(artifact_path)
            manifest["artifacts"][profile_type][artifact_type] = {
                "path": str(artifact_path.relative_to(REPO_ROOT)),
                "sha256": hash_value,
                "size_bytes": artifact_path.stat().st_size,
                "last_verified": datetime.now().isoformat()[:10]
            }
            print(f"  [{artifact_type.upper()}] {hash_value[:16]}... ({artifact_path.stat().st_size} bytes)")
            updated_count += 1

    if updated_count > 0:
        save_golden_manifest(manifest)

    print(f"\n[DONE] {updated_count} Hashes aktualisiert")
    return True


def request_login_code(base_url: str, email: str) -> None:
    """Fordert einen Login-Code an."""
    if requests is None:
        raise ImportError("requests module required for API access")

    url = f"{base_url}/auth/request-code"
    print(f"[auth] Request-Code anfordern: {url} → {email}")
    resp = requests.post(url, json={"email": email}, timeout=10)
    resp.raise_for_status()
    print(f"[auth] Login-Code an {email} gesendet.")


def login(session: "requests.Session", base_url: str, email: str, code: str) -> None:
    """Meldet sich mit Code an."""
    url = f"{base_url}/auth/login"
    print(f"[auth] Login: {url}")
    resp = session.post(url, json={"email": email, "code": code}, timeout=10)
    resp.raise_for_status()
    print("[auth] Login erfolgreich.")


def generate_report_via_api(
    session: "requests.Session",
    base_url: str,
    profile: Dict[str, Any],
    profile_type: str
) -> Tuple[Optional[bytes], Optional[bytes]]:
    """
    Generiert einen Report via API und lädt HTML/PDF.

    Returns:
        Tuple[Optional[bytes], Optional[bytes]]: (html_content, pdf_content)
    """
    # Submit briefing
    payload = {
        "lang": profile.get("lang", "de"),
        "answers": profile["answers"]
    }

    url = f"{base_url}/briefings/submit"
    print(f"  [API] Sende Briefing an {url}...")

    try:
        resp = session.post(url, json=payload, timeout=300)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"  [ERROR] API-Aufruf fehlgeschlagen: {e}")
        return None, None

    briefing_id = data.get("briefing_id")
    if not briefing_id:
        print(f"  [ERROR] Keine briefing_id im Response")
        return None, None

    print(f"  [OK] Briefing erstellt: {briefing_id}")

    # Warte auf Report-Generierung
    print(f"  [WAIT] Warte auf Report-Generierung...")
    time.sleep(30)

    # Lade HTML
    html_content = None
    try:
        html_url = f"{base_url}/reports/{briefing_id}/html"
        resp = session.get(html_url, timeout=60)
        if resp.status_code == 200:
            html_content = resp.content
            print(f"  [OK] HTML geladen ({len(html_content)} bytes)")
    except Exception as e:
        print(f"  [WARN] HTML-Download fehlgeschlagen: {e}")

    # Lade PDF
    pdf_content = None
    try:
        pdf_url = f"{base_url}/reports/{briefing_id}/pdf"
        resp = session.get(pdf_url, timeout=120)
        if resp.status_code == 200:
            pdf_content = resp.content
            print(f"  [OK] PDF geladen ({len(pdf_content)} bytes)")
    except Exception as e:
        print(f"  [WARN] PDF-Download fehlgeschlagen: {e}")

    return html_content, pdf_content


def generate_golden_reports(base_url: str, email: str, force: bool = False) -> bool:
    """Generiert Golden Reports für alle Release-Profile."""
    if requests is None:
        print("[ERROR] requests module nicht installiert. Bitte 'pip install requests' ausführen.")
        return False

    print("\n" + "=" * 78)
    print("GOLDEN REPORT GENERATION")
    print("=" * 78)

    # Prüfe auf existierende Artifacts
    for profile_type in RELEASE_PROFILES:
        existing = check_existing_artifacts(profile_type)
        if existing and not force:
            print(f"\n[ERROR] Golden Reports für '{profile_type}' existieren bereits!")
            print(f"  Existierende Artifacts: {list(existing.keys())}")
            print(f"\n  Verwende --force um zu überschreiben.")
            print(f"  WARNUNG: Golden Reports dürfen NICHT automatisch überschrieben werden!")
            return False

    # Login
    try:
        request_login_code(base_url, email)
    except Exception as e:
        print(f"[auth] FEHLER beim Anfordern des Login-Codes: {e}")
        return False

    code = input("Bitte Login-Code aus der E-Mail eingeben: ").strip()
    if not code:
        print("[auth] Kein Code eingegeben, breche ab.")
        return False

    session = requests.Session()
    try:
        login(session, base_url, email, code)
    except Exception as e:
        print(f"[auth] FEHLER beim Login: {e}")
        return False

    # Generiere Reports
    manifest = load_golden_manifest()
    success_count = 0

    for profile_type in RELEASE_PROFILES:
        print(f"\n{'=' * 78}")
        print(f"[{profile_type.upper()}] Generiere Golden Report...")
        print("=" * 78)

        profile = load_release_profile(profile_type)
        if not profile:
            continue

        html_content, pdf_content = generate_report_via_api(
            session, base_url, profile, profile_type
        )

        profile_dir = GOLDEN_REPORTS_DIR / profile_type
        profile_dir.mkdir(parents=True, exist_ok=True)

        if profile_type not in manifest["artifacts"]:
            manifest["artifacts"][profile_type] = {}

        # Speichere HTML
        if html_content:
            html_path = profile_dir / f"golden_report_{profile_type}.html"
            with open(html_path, "wb") as f:
                f.write(html_content)

            hash_value = compute_sha256(html_path)
            manifest["artifacts"][profile_type]["html"] = {
                "path": str(html_path.relative_to(REPO_ROOT)),
                "sha256": hash_value,
                "size_bytes": len(html_content),
                "generated_date": datetime.now().isoformat()[:10]
            }
            print(f"  [SAVED] HTML: {html_path}")
            print(f"  [HASH]  {hash_value}")

        # Speichere PDF
        if pdf_content:
            pdf_path = profile_dir / f"golden_report_{profile_type}.pdf"
            with open(pdf_path, "wb") as f:
                f.write(pdf_content)

            hash_value = compute_sha256(pdf_path)
            manifest["artifacts"][profile_type]["pdf"] = {
                "path": str(pdf_path.relative_to(REPO_ROOT)),
                "sha256": hash_value,
                "size_bytes": len(pdf_content),
                "generated_date": datetime.now().isoformat()[:10]
            }
            print(f"  [SAVED] PDF: {pdf_path}")
            print(f"  [HASH]  {hash_value}")

        if html_content or pdf_content:
            success_count += 1

        # Pause zwischen Profilen
        time.sleep(20)

    # Speichere Manifest
    save_golden_manifest(manifest)

    print(f"\n{'=' * 78}")
    print(f"GENERATION ABGESCHLOSSEN: {success_count}/{len(RELEASE_PROFILES)} Profile erfolgreich")
    print("=" * 78)

    return success_count == len(RELEASE_PROFILES)


def verify_golden_reports() -> Tuple[bool, List[str]]:
    """
    Verifiziert alle Golden Reports gegen das Manifest.

    Returns:
        Tuple[bool, List[str]]: (all_valid, list_of_issues)
    """
    print("\n" + "=" * 78)
    print("GOLDEN REPORT VERIFICATION")
    print("=" * 78)

    if not GOLDEN_MANIFEST_PATH.exists():
        return False, ["golden_manifest.json nicht gefunden"]

    manifest = load_golden_manifest()
    issues: List[str] = []

    for profile_type in RELEASE_PROFILES:
        profile_artifacts = manifest.get("artifacts", {}).get(profile_type, {})

        if not profile_artifacts:
            issues.append(f"[{profile_type}] Keine Artifacts im Manifest")
            continue

        print(f"\n[{profile_type}] Verifiziere Artifacts...")

        for artifact_type, artifact_info in profile_artifacts.items():
            artifact_path = REPO_ROOT / artifact_info["path"]

            if not artifact_path.exists():
                issues.append(f"[{profile_type}/{artifact_type}] Datei nicht gefunden: {artifact_path}")
                continue

            expected_hash = artifact_info["sha256"]
            actual_hash = compute_sha256(artifact_path)

            if expected_hash != actual_hash:
                issues.append(
                    f"[{profile_type}/{artifact_type}] Hash-Mismatch!\n"
                    f"    Erwartet: {expected_hash}\n"
                    f"    Aktuell:  {actual_hash}"
                )
                print(f"  [{artifact_type.upper()}] HASH MISMATCH!")
            else:
                print(f"  [{artifact_type.upper()}] OK ({actual_hash[:16]}...)")

    if issues:
        print(f"\n[FAILED] {len(issues)} Probleme gefunden:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print(f"\n[PASSED] Alle Golden Reports verifiziert")

    return len(issues) == 0, issues


def main() -> None:
    parser = argparse.ArgumentParser(
        description="PLATIN+++ Golden Report Generator und Verifier"
    )
    parser.add_argument(
        "--base-url",
        default="https://make.ki-sicherheit.jetzt/api",
        help="Basis-URL des Backends (ohne trailing Slash)"
    )
    parser.add_argument(
        "--email",
        default="wolf.hohl@web.de",
        help="E-Mail für Login-Code"
    )
    parser.add_argument(
        "--hash-only",
        action="store_true",
        help="Nur Hashes für existierende Artifacts aktualisieren"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verifiziere Golden Reports gegen Manifest"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Überschreibe existierende Golden Reports (WARNUNG: Audit-Trail!)"
    )
    args = parser.parse_args()

    # Stelle sicher, dass Verzeichnisse existieren
    GOLDEN_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    for profile_type in RELEASE_PROFILES:
        (GOLDEN_REPORTS_DIR / profile_type).mkdir(parents=True, exist_ok=True)

    if args.verify:
        is_valid, issues = verify_golden_reports()
        sys.exit(0 if is_valid else 1)

    if args.hash_only:
        success = update_hashes_only()
        sys.exit(0 if success else 1)

    # Generiere Golden Reports
    base_url = args.base_url.rstrip("/")
    success = generate_golden_reports(base_url, args.email, args.force)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
