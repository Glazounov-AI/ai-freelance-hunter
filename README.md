# AI Freelance Hunter

Independent Python project for finding and evaluating freelance opportunities.

## Foundation (Block A)

Implemented: FastAPI, PostgreSQL models, Alembic migration, secure admin-token routes,
Docker Compose, source/analyzer contracts, tests and CI. **No scraping, AI calls or proposal
sending are enabled.**

### Prerequisites

- Docker Desktop with Compose
- PowerShell 7
- Python 3.12 for local tests (Docker uses Python 3.12)

### First start (PowerShell)

```powershell
.\scripts\init-env.ps1
docker compose config --quiet
docker compose up -d --build
docker compose ps
Invoke-RestMethod http://127.0.0.1:8000/health/live
```

**Never commit `.env`**. PostgreSQL passwords with URL-special characters must be
percent-encoded in `DATABASE_URL`; simplest is to generate a hex-only password.

### Authorized endpoint

```powershell
$token = (Get-Content .env | Where-Object { $_ -match '^ADMIN_API_TOKEN=' }) -replace '^ADMIN_API_TOKEN=', ''
Invoke-RestMethod http://127.0.0.1:8000/api/v1/status -Headers @{ 'X-Admin-Token' = $token }
```

### Tests

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
```

### Important

- Compose publishes the API only on `127.0.0.1:8000`.
- `GET /health/live` is public and does not reveal secrets.
- `GET /health/ready` and `/api/v1/status` require `X-Admin-Token`.
- `migrate` is a one-shot Compose service.
- This is a development foundation, not a production security certification.
