# Railway DB-Console Display-Inkonsistenz

**Beobachtet:** 2026-04-28
**Verifiziert:** TODO

## Symptom

Am 28.04.2026 zeigte die Railway DB-Console widersprüchliche Ergebnisse in derselben Session:

```sql
-- Query 1
SELECT MAX(id), COUNT(*) FROM briefings;
-- Ergebnis: max=1062, count=1062

-- Query 2 (gleiche Session, kurz danach)
SELECT id, status, source, created_at
  FROM briefings
 ORDER BY id DESC
 LIMIT 10;
-- Ergebnis: 0 rows
```

Daten existieren definitiv (E-Mail-Versand der Reports an `bewertung@ki-sicherheit.jetzt` ist erfolgt, IDs 1052–1062 in Subject-Lines sichtbar).

## Reproduktion

- Reproduzierbar: TODO (ja / nein / intermittierend)
- Bedingungen: TODO

## Test-Ergebnisse

### Test 1 — psql direkt (via Railway CLI)

```
TODO: psql output here
```

Verhalten: TODO (✅ korrekt / ❌ ebenfalls leer)

### Test 2 — Backend-Admin-API

```
TODO: curl output here
```

Verhalten: TODO (✅ korrekt / ❌ ebenfalls leer)

### Test 3 — Console-Variationen

| Variante | Query | Rows zurückgegeben |
|----------|-------|--------------------|
| a) ohne ORDER BY | `SELECT id FROM briefings LIMIT 5;` | TODO |
| b) mit WHERE | `SELECT id FROM briefings WHERE id > 0 ORDER BY id DESC LIMIT 5;` | TODO |
| c) andere Tabelle | `SELECT COUNT(*) FROM users;` | TODO |
| d) nach Hard-Refresh | Original-Query nochmal | TODO |
| e) eine Spalte | `SELECT id FROM briefings ORDER BY id DESC LIMIT 10;` | TODO |

### Test 4 — Browser DevTools (falls Bug noch reproduzierbar)

TODO: Network-Tab-Befund — Backend-Response leer oder gefüllt?

## Diagnose

TODO: Hypothese mit Evidenz aus Tests

Mögliche Ursachen:
- (i) Railway-DB-Console-UI-Bug (Frontend-Rendering)
- (ii) Read-only-Replica mit Lag
- (iii) Timezone- oder Caching-Problem
- (iv) Permissions/Row-Level-Security-Effekt

## Workaround

Empfohlen, bis Bug-Quelle geklärt:

- **Für DB-Recherche:** `railway connect Postgres-_HAO` → psql in Terminal statt Console-UI
- **Für Admin-Recherche:** `GET /api/admin/briefings/recent?hours=N` mit Wolf-JWT
- **Für Console-UI:** ggf. `ORDER BY` weglassen, manuell sortieren

## Empfehlung

- [ ] Bug-Report an Railway: TODO (ja / nein)
- [ ] Workaround in Team-Doku ergänzen: TODO

---

**Status:** Skeleton — wartet auf Test-Ergebnisse von Wolf.
