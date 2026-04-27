# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, **please do not open a public GitHub issue**.

Instead, report it privately to:

- **Email:** wolf@ki-sicherheit.jetzt
- **Subject prefix:** `[SECURITY] api-ki-backend-neu — <short-summary>`

Please include, where possible:

- A description of the issue and its impact
- Steps to reproduce, or a minimal proof-of-concept
- The affected version / commit hash
- Any suggested mitigation

You will receive an acknowledgement within **3 business days**.
We aim to provide an initial assessment within **7 business days** and a coordinated disclosure timeline thereafter.

## Supported Versions

The `main` branch is the only actively supported version. Forks and historical branches are not maintained for security fixes.

## Scope

In scope:

- The Python backend code in this repository
- CI workflows in `.github/workflows/`
- Direct production dependencies pinned in `requirements.txt`

Out of scope:

- The hosted Railway deployment (report directly via email)
- Third-party services (OpenAI, Anthropic, Tavily, Perplexity, Resend) — please report to the vendor
- Social engineering, physical security, denial-of-service via traffic volume

## Safe Harbour

Good-faith security research that follows this policy is welcome.
We will not pursue legal action against researchers who:

- Avoid privacy violations and service degradation
- Do not exfiltrate user data beyond what is necessary to demonstrate the issue
- Give us a reasonable time to address the issue before any public disclosure
