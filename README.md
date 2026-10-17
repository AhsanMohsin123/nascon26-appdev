# NaSCon '26 — App Dev: Multi-Sport League & Club Operations Platform

**Stack:** Python FastAPI (backend) · Flutter (mobile)

## Quick Start

```bash
# Set your team salt from the slip
export DAY1_SALT=<your-salt>

# Bring up the full backend (API on :8080)
docker compose up -d --build

# Verify health
curl http://localhost:8080/health
```

The stack seeds baseline data automatically on first start.

## Demo Accounts

| Role | Email | Password |
|------|-------|----------|
| Platform Super-Admin | admin@nascon.test | Nascon@26 |
| League Organizer (owns league-alpha-1) | organizer@nascon.test | Nascon@26 |
| Club Manager (owns club-alpha-1) | manager@nascon.test | Nascon@26 |
| Player (player-alpha-1) | player@nascon.test | Nascon@26 |
| General Viewer | viewer@nascon.test | Nascon@26 |

## Repository Structure

```
backend/          Python FastAPI application
  app/
    api/          Route handlers (/audit/v1/*, /api/v1/*)
    domain/       Domain services (leagues, fixtures, scoring, roster, store)
    models/       SQLAlchemy ORM models
    schemas/      Pydantic request/response schemas
    worker.py     Celery background worker
  tests/          pytest test suite
  Dockerfile
mobile/           Flutter application
  lib/
  release/        app-release.apk (Android build)
docker-compose.yml
TRACEABILITY.md
COVERAGE.json
```

## Running Tests

```bash
bash run_tests.sh
```

## Mobile App

The Flutter app connects to the backend. Configure the server address in Settings:
- Android emulator: `10.0.2.2:8080`
- Physical device: `<laptop-LAN-IP>:8080`

Android APK: `mobile/release/app-release.apk`
