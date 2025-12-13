# PLATIN+++ Release-Readiness Dokumentation

**Version:** 1.0.0
**Datum:** 2025-12-13
**Status:** Produktiv

---

## 1. Zweck von Release-Profilen

Release-Profile sind **stabile, versionierbare Referenz-Inputs** für das PLATIN+++ Backend. Sie dienen als:

- **Auslieferungsreferenz:** Offizielle Test-Inputs für Release-Validierung
- **Audit-Grundlage:** Dokumentierte, unveränderliche Testfälle
- **Regressionsbasis:** Vergleichsstandard für neue Versionen

### Abgrenzung zu anderen Profilen

| Profiltyp | Zweck | Veränderbar | Ablageort |
|-----------|-------|-------------|-----------|
| **Release-Profile** | Offizielle Auslieferungsreferenz | Nur mit Versionssprung | `data/release_profiles/` |
| Test-Profile Gold | Entwicklungs-Testfälle | Ja | `data/test_profiles_gold/` |
| Test-Profile Optimized | Auto-generierte/optimierte Profile | Ja | `data/test_profiles_gold_optimized/` |

### Wichtige Regeln

1. **Read-Only:** Release-Profile dürfen nicht automatisch verändert werden
2. **Keine Ableitung:** Niemals aus `_optimized`-Profilen abgeleitet
3. **Versionssprung:** Änderungen erfordern `release_version` Erhöhung
4. **Manuelle Prüfung:** Jedes Profil muss manuell validiert sein

---

## 2. Ablauf eines Release-Checks

### 2.1 Schnell-Check (Offline)

```bash
# Vollständiger Release-Check
python scripts/generate_test_reports.py --release-check

# Oder direkt:
python scripts/release_check.py --verbose
```

### 2.2 Was wird geprüft?

| Check | Beschreibung | Fehler-Verhalten |
|-------|--------------|------------------|
| **Release-Profile** | Existenz & Gültigkeit der Profile | Exit 2 |
| **Golden Manifest** | Existenz & Struktur des Manifests | Exit 3 |
| **Hash-Integrität** | SHA-256 Vergleich mit Manifest | Exit 1 |
| **Consistency** | Persona-Match, Sprache, Felder | Exit 5 |

### 2.3 Ausgabe-Beispiel

```
============================================================
PLATIN+++ RELEASE-CHECK
============================================================
Zeitstempel: 2025-12-13T12:00:00
Modus: Vollständig
API-Check: Nein

============================================================
CHECK 1: Release-Profile Validierung
============================================================
  [solo] OK (v1.0.0)
  [team] OK (v1.0.0)
  [kmu]  OK (v1.0.0)

...

============================================================
RELEASE-CHECK ZUSAMMENFASSUNG
============================================================

Checks: 9/9 bestanden

------------------------------------------------------------
STATUS: BESTANDEN
------------------------------------------------------------
```

---

## 3. Update-Prozess für Golden Reports

### 3.1 Wann neue Golden Reports erstellen?

Neue Golden Reports sind erforderlich bei:

- **Major-Version** des PLATIN+++ Backends
- **Änderungen an Release-Profilen**
- **Änderungen an kritischen Rendering-Komponenten**

### 3.2 Generierungs-Workflow

```bash
# 1. Golden Reports generieren (erfordert API-Zugang)
python scripts/generate_golden_reports.py \
  --base-url https://make.ki-sicherheit.jetzt/api \
  --email your@email.com

# 2. Bei existierenden Reports: --force erforderlich
python scripts/generate_golden_reports.py \
  --base-url https://make.ki-sicherheit.jetzt/api \
  --email your@email.com \
  --force

# 3. Nur Hashes aktualisieren (ohne neue Reports)
python scripts/generate_golden_reports.py --hash-only

# 4. Verifizierung
python scripts/generate_golden_reports.py --verify
```

### 3.3 Wichtige Hinweise

- Golden Reports dürfen **NICHT automatisch** überschrieben werden
- `--force` Flag erzeugt Audit-Trail
- Nach Generierung: Commit der neuen Artifacts + Manifest

---

## 4. Verzeichnisstruktur

```
api-ki-backend-neu/
├── data/
│   └── release_profiles/        # Release-Profile
│       ├── manifest.json        # Profil-Manifest
│       ├── solo/
│       │   └── profile.json     # Solo-Release-Profil
│       ├── team/
│       │   └── profile.json     # Team-Release-Profil
│       └── kmu/
│           └── profile.json     # KMU-Release-Profil
│
├── artifacts/
│   └── golden_reports/          # Golden Report Artifacts
│       ├── golden_manifest.json # Hash-Manifest
│       ├── solo/
│       │   ├── golden_report_solo.html
│       │   └── golden_report_solo.pdf
│       ├── team/
│       │   └── ...
│       └── kmu/
│           └── ...
│
├── docs/
│   └── platin_release/          # Release-Dokumentation
│       ├── README.md            # Diese Datei
│       └── failure_modes.md     # Auto-Healing-Grenzen
│
└── scripts/
    ├── generate_test_reports.py # Test-Report-Generator (+ --release-check)
    ├── generate_golden_reports.py # Golden Report Generator
    └── release_check.py         # Release-Validation-Check
```

---

## 5. CLI-Referenz

### generate_test_reports.py

```bash
# Standard-Nutzung (Test-Profile)
python scripts/generate_test_reports.py --base-url <URL> --email <EMAIL>

# PLATIN+ Gold-Standard Profile
python scripts/generate_test_reports.py --platin-only

# Release-Check Modus (NEU)
python scripts/generate_test_reports.py --release-check
```

### release_check.py

```bash
# Vollständiger Check
python scripts/release_check.py

# Nur Hash-Validierung
python scripts/release_check.py --hash-only

# JSON-Ausgabe (für CI)
python scripts/release_check.py --json

# Verbose
python scripts/release_check.py --verbose
```

### generate_golden_reports.py

```bash
# Golden Reports generieren
python scripts/generate_golden_reports.py --base-url <URL> --email <EMAIL>

# Nur Hashes aktualisieren
python scripts/generate_golden_reports.py --hash-only

# Verifizierung
python scripts/generate_golden_reports.py --verify

# Überschreiben (mit Audit-Trail)
python scripts/generate_golden_reports.py --force
```

---

## 6. Exit Codes

| Code | Bedeutung | Aktion |
|------|-----------|--------|
| 0 | Erfolg | - |
| 1 | Hash-Mismatch | Golden Reports prüfen |
| 2 | Release-Profil fehlt | Profile erstellen |
| 3 | Manifest fehlt | Manifest generieren |
| 4 | Artifact fehlt | Golden Reports generieren |
| 5 | Consistency-Fehler | Profile korrigieren |
| 6 | Fallback erkannt | Nicht im Release-Modus erlaubt |
| 7 | API-Fehler | Backend prüfen |

---

## 7. Integration in CI/CD

### GitHub Actions Beispiel

```yaml
release-check:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4

    - name: Setup Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install Dependencies
      run: pip install -r requirements.txt

    - name: Run Release Check
      run: python scripts/release_check.py --json
```

---

## 8. Troubleshooting

### "Hash Mismatch" Fehler

```
Ursache: Golden Report wurde nach Manifest-Erstellung verändert
Lösung:  python scripts/generate_golden_reports.py --hash-only
```

### "Release-Profil fehlt" Fehler

```
Ursache: Profil-Datei existiert nicht
Lösung:  Profil in data/release_profiles/<typ>/profile.json erstellen
```

### "Pending Generation" Warnung

```
Ursache: Golden Reports wurden noch nicht generiert
Lösung:  python scripts/generate_golden_reports.py --base-url <URL> --email <EMAIL>
```

---

## 9. Referenzen

- [failure_modes.md](./failure_modes.md) - Auto-Healing-Grenzen
- [ARCHITECTURE.md](../ARCHITECTURE.md) - System-Architektur
- [services/auto_healing.py](../../services/auto_healing.py) - Auto-Healing-Implementation
- [services/consistency_engine.py](../../services/consistency_engine.py) - G22 Consistency Engine
