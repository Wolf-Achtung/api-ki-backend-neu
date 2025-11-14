#!/usr/bin/env python3
"""
Test-Script für den Login-Flow
Simuliert den kompletten Login-Prozess und testet die Token-Validierung
"""
import requests
import json
import time

# API-Base URL (passe diese an)
API_BASE = "https://api-ki-backend-neu-production.up.railway.app/api"
# Alternativ lokal: API_BASE = "http://localhost:8080/api"

# Test-Email (ersetze mit deiner Email)
TEST_EMAIL = "wolf.hohl@web.de"

def test_request_code():
    """Schritt 1: Code anfordern"""
    print("=" * 60)
    print("SCHRITT 1: Code anfordern")
    print("=" * 60)

    url = f"{API_BASE}/auth/request-code"
    payload = {"email": TEST_EMAIL}

    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(url, json=payload)
        print(f"\nStatus: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")

        if response.status_code == 204:
            print("✅ Code wurde erfolgreich angefordert!")
            print("📧 Bitte prüfe deine E-Mail und gib den Code unten ein.")
            return True
        else:
            print(f"❌ Fehler: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def test_login(code):
    """Schritt 2: Mit Code einloggen"""
    print("\n" + "=" * 60)
    print("SCHRITT 2: Login mit Code")
    print("=" * 60)

    url = f"{API_BASE}/auth/login"
    payload = {"email": TEST_EMAIL, "code": code}

    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(url, json=payload)
        print(f"\nStatus: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")

        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Login erfolgreich!")
            print(f"Response: {json.dumps(data, indent=2)}")

            token = data.get("access_token")
            if token:
                print(f"\n🔑 Token: {token[:20]}...{token[-20:]}")
                print(f"Token-Länge: {len(token)}")
                return token
            else:
                print("❌ Kein access_token in der Response!")
                return None
        else:
            print(f"❌ Fehler: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None


def test_token_validation(token):
    """Schritt 3: Token validieren mit Debug-Endpoint"""
    print("\n" + "=" * 60)
    print("SCHRITT 3: Token-Validierung testen")
    print("=" * 60)

    url = f"{API_BASE}/auth/debug"
    headers = {"Authorization": f"Bearer {token}"}

    print(f"GET {url}")
    print(f"Headers: Authorization: Bearer {token[:20]}...{token[-20:]}")

    try:
        response = requests.get(url, headers=headers)
        print(f"\nStatus: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Debug-Endpoint erreicht!")
            print(f"Response: {json.dumps(data, indent=2)}")

            # Überprüfe Token-Validierung
            token_info = data.get("token_info", {})
            if token_info.get("verified"):
                print(f"\n✅ Token ist GÜLTIG!")
                print(f"User-Email: {token_info.get('verified_email')}")
            else:
                print(f"\n❌ Token ist UNGÜLTIG!")
                print(f"Fehler: {token_info.get('verify_error')}")

            return token_info.get("verified", False)
        else:
            print(f"❌ Fehler: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def test_protected_endpoint(token):
    """Schritt 4: Geschützten Endpoint testen (z.B. /admin/overview)"""
    print("\n" + "=" * 60)
    print("SCHRITT 4: Geschützten Endpoint testen")
    print("=" * 60)

    # Versuche verschiedene Endpoints
    endpoints = [
        "/briefings/debug",
        "/debug/config",
    ]

    for endpoint in endpoints:
        url = f"{API_BASE}{endpoint}"
        headers = {"Authorization": f"Bearer {token}"}

        print(f"\nGET {url}")

        try:
            response = requests.get(url, headers=headers)
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                print(f"✅ Endpoint erreichbar!")
                data = response.json()
                if endpoint == "/briefings/debug":
                    authenticated = data.get("authenticated", False)
                    print(f"Authenticated: {authenticated}")
                    if authenticated:
                        print(f"User: {data.get('user_email')}")
            else:
                print(f"❌ Fehler: {response.status_code}")
        except Exception as e:
            print(f"❌ Exception: {e}")


def main():
    print("\n" + "=" * 60)
    print("LOGIN-FLOW TEST")
    print("=" * 60)
    print(f"API-Base: {API_BASE}")
    print(f"Test-Email: {TEST_EMAIL}")
    print()

    # Schritt 1: Code anfordern
    if not test_request_code():
        print("\n❌ Code-Anforderung fehlgeschlagen. Abbruch.")
        return

    # Warte auf Eingabe des Codes
    print()
    code = input("Bitte Code aus der E-Mail eingeben: ").strip()

    if not code:
        print("❌ Kein Code eingegeben. Abbruch.")
        return

    # Schritt 2: Login
    token = test_login(code)
    if not token:
        print("\n❌ Login fehlgeschlagen. Abbruch.")
        return

    # Schritt 3: Token validieren
    if not test_token_validation(token):
        print("\n❌ Token-Validierung fehlgeschlagen!")
        print("Das könnte das Problem sein, warum du zurück zur Login-Seite geleitet wirst.")
        return

    # Schritt 4: Geschützte Endpoints testen
    test_protected_endpoint(token)

    print("\n" + "=" * 60)
    print("TEST ABGESCHLOSSEN")
    print("=" * 60)


if __name__ == "__main__":
    main()
