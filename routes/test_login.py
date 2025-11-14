# -*- coding: utf-8 -*-
"""Test Login Page Router - Provides HTML test interface"""
from __future__ import annotations

from fastapi import APIRouter, Response
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/test", tags=["testing"])

@router.get("/login", response_class=HTMLResponse)
def login_test_page():
    """Serves the login test HTML page"""
    html_content = """<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KI-Backend Login Test</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; padding: 20px;
        }
        .container {
            max-width: 800px; margin: 0 auto; background: white;
            border-radius: 12px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 30px; text-align: center;
        }
        .header h1 { font-size: 28px; margin-bottom: 10px; }
        .header p { opacity: 0.9; }
        .content { padding: 30px; }
        .section {
            margin-bottom: 30px; padding: 20px; background: #f8f9fa;
            border-radius: 8px; border-left: 4px solid #667eea;
        }
        .section h2 { color: #333; margin-bottom: 15px; font-size: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; color: #555; font-weight: 500; }
        input {
            width: 100%; padding: 12px; border: 2px solid #e1e4e8;
            border-radius: 6px; font-size: 14px; transition: border-color 0.3s;
        }
        input:focus { outline: none; border-color: #667eea; }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; border: none; padding: 12px 24px; border-radius: 6px;
            font-size: 16px; font-weight: 600; cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4); }
        button:active { transform: translateY(0); }
        button:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        .log {
            background: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 6px;
            font-family: 'Courier New', monospace; font-size: 13px;
            max-height: 400px; overflow-y: auto; white-space: pre-wrap; word-wrap: break-word;
        }
        .log-entry { margin-bottom: 8px; padding: 8px; border-radius: 4px; }
        .log-info { background: rgba(66, 153, 225, 0.1); border-left: 3px solid #4299e1; }
        .log-success { background: rgba(72, 187, 120, 0.1); border-left: 3px solid #48bb78; }
        .log-error { background: rgba(245, 101, 101, 0.1); border-left: 3px solid #f56565; }
        .log-warning { background: rgba(237, 137, 54, 0.1); border-left: 3px solid #ed8936; }
        .timestamp { color: #888; font-size: 11px; }
        .token-display {
            background: #f0f4f8; border: 2px solid #667eea; border-radius: 6px;
            padding: 15px; margin-top: 15px; word-wrap: break-word;
        }
        .token-display strong { color: #667eea; display: block; margin-bottom: 8px; }
        .token-value {
            background: white; padding: 10px; border-radius: 4px;
            font-family: monospace; font-size: 12px; color: #333;
            max-height: 100px; overflow-y: auto;
        }
        .clear-btn { background: #718096; margin-top: 10px; }
        .info-box {
            background: #e6fffa; border: 1px solid #81e6d9;
            border-radius: 6px; padding: 15px; margin-bottom: 20px;
        }
        .info-box strong { color: #234e52; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 KI-Backend Login Test</h1>
            <p>Debugging-Tool für Authentication</p>
        </div>
        <div class="content">
            <div class="info-box">
                <strong>📝 Anleitung:</strong><br>
                Backend-URL ist bereits gesetzt (aktueller Server)<br>
                1. E-Mail eingeben und Code anfordern<br>
                2. Code aus E-Mail kopieren und einloggen<br>
                3. Logs prüfen um Details zu sehen
            </div>
            <div class="section">
                <h2>1️⃣ Login-Code anfordern</h2>
                <div class="form-group">
                    <label>E-Mail Adresse:</label>
                    <input type="email" id="email" placeholder="ihre@email.de">
                </div>
                <button id="requestCodeBtn" onclick="requestCode()">📧 Code per E-Mail anfordern</button>
            </div>
            <div class="section">
                <h2>2️⃣ Mit Code einloggen</h2>
                <div class="form-group">
                    <label>Login-Code (aus E-Mail):</label>
                    <input type="text" id="code" placeholder="123456" maxlength="6">
                </div>
                <button id="loginBtn" onclick="login()">🔑 Einloggen</button>
            </div>
            <div class="section" id="tokenSection" style="display: none;">
                <h2>✅ Login erfolgreich!</h2>
                <div class="token-display">
                    <strong>Access Token:</strong>
                    <div class="token-value" id="tokenValue"></div>
                </div>
            </div>
            <div class="section">
                <h2>📊 Debug Logs</h2>
                <div class="log" id="logOutput"></div>
                <button class="clear-btn" onclick="clearLogs()">🗑️ Logs löschen</button>
            </div>
        </div>
    </div>
    <script>
        const backendUrl = window.location.origin;

        function log(message, type = 'info') {
            const logOutput = document.getElementById('logOutput');
            const timestamp = new Date().toLocaleTimeString('de-DE');
            const entry = document.createElement('div');
            entry.className = `log-entry log-${type}`;
            let icon = '📝';
            if (type === 'success') icon = '✅';
            if (type === 'error') icon = '❌';
            if (type === 'warning') icon = '⚠️';
            entry.innerHTML = `<span class="timestamp">[${timestamp}]</span> ${icon} ${message}`;
            logOutput.appendChild(entry);
            logOutput.scrollTop = logOutput.scrollHeight;
        }

        function clearLogs() {
            document.getElementById('logOutput').innerHTML = '';
            log('Logs gelöscht', 'info');
        }

        async function requestCode() {
            const email = document.getElementById('email').value.trim();
            const btn = document.getElementById('requestCodeBtn');
            if (!email) {
                log('❌ E-Mail fehlt!', 'error');
                alert('Bitte E-Mail Adresse eingeben');
                return;
            }
            btn.disabled = true;
            log(`📤 Sende Code-Anforderung an: ${backendUrl}/api/auth/request-code`, 'info');
            log(`📧 E-Mail: ${email}`, 'info');
            try {
                const response = await fetch(`${backendUrl}/api/auth/request-code`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email })
                });
                log(`📥 Response Status: ${response.status} ${response.statusText}`,
                    response.ok ? 'success' : 'error');
                if (response.ok) {
                    log('✅ Code wurde versendet! Prüfen Sie Ihre E-Mails.', 'success');
                    alert('✅ Code wurde versendet!\\n\\nPrüfen Sie Ihre E-Mails.');
                } else {
                    const errorData = await response.text();
                    log(`❌ Fehler: ${errorData}`, 'error');
                    alert(`Fehler: ${response.status} - ${errorData}`);
                }
            } catch (error) {
                log(`❌ Netzwerkfehler: ${error.message}`, 'error');
                alert(`Netzwerkfehler: ${error.message}`);
            } finally {
                btn.disabled = false;
            }
        }

        async function login() {
            const email = document.getElementById('email').value.trim();
            const code = document.getElementById('code').value.trim();
            const btn = document.getElementById('loginBtn');
            if (!email || !code) {
                log('❌ E-Mail oder Code fehlt!', 'error');
                alert('Bitte E-Mail und Code eingeben');
                return;
            }
            btn.disabled = true;
            log(`📤 Sende Login-Request an: ${backendUrl}/api/auth/login`, 'info');
            log(`📧 E-Mail: ${email}`, 'info');
            log(`🔑 Code: ${code}`, 'info');
            try {
                const response = await fetch(`${backendUrl}/api/auth/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, code })
                });
                log(`📥 Response Status: ${response.status} ${response.statusText}`,
                    response.ok ? 'success' : 'error');
                const responseData = await response.json();
                log(`📦 Response: ${JSON.stringify(responseData, null, 2)}`, 'info');
                if (response.ok && responseData.access_token) {
                    const token = responseData.access_token;
                    log(`✅ Login erfolgreich! Token-Länge: ${token.length}`, 'success');
                    localStorage.setItem('access_token', token);
                    document.getElementById('tokenSection').style.display = 'block';
                    document.getElementById('tokenValue').textContent = token;
                    alert('✅ Login erfolgreich!\\n\\nToken wurde gespeichert.');
                } else {
                    log(`❌ Login fehlgeschlagen`, 'error');
                    alert(`❌ Login fehlgeschlagen: ${responseData.detail || 'Unbekannter Fehler'}`);
                }
            } catch (error) {
                log(`❌ Fehler: ${error.message}`, 'error');
                alert(`Fehler: ${error.message}`);
            } finally {
                btn.disabled = false;
            }
        }

        log('🚀 Login-Test Tool gestartet', 'success');
        log(`🌐 Backend URL: ${backendUrl}`, 'info');
    </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)
