# Block E — operator dashboard

- URL: `http://127.0.0.1:9000/dashboard/login`.
- Log in with the existing `ADMIN_API_TOKEN` from `.env`. It is submitted to the server, never placed in JS or localStorage.
- Session cookie is signed, HttpOnly, SameSite=Strict, expires after 8 hours. When accessed via HTTPS, Secure is enabled.
- Browser writes require a session and `X-CSRF-Token` header. Existing API endpoints retain their independent `X-Admin-Token` protection.
- The UI is read-only for opportunities and AI analysis. It supports creating an application from an existing analysis, editing a draft, approving/rejecting and viewing the audit history.
- It does **not** send messages to freelance sites.
- No DB migration required. Files in `app/web/static/` are packaged by the Dockerfile's existing `COPY app ./app`.
- Development access is limited to localhost by `compose.yaml`. Do not expose dashboard directly to the internet without HTTPS, a rate limiter for login attempts, and a production-ready session strategy.
- For now, the dashboard uses a single operator credential, not individual user accounts. Audit events cannot identify separate operators.

## Checks

```powershell
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
docker compose -f compose.yaml -f compose.ai.yaml up -d --build
```

Open `/dashboard/login` and test the existing application flow. Do not run against an environment containing production orders until reviewed.
