# Traceability Matrix — NaSCon '26 App Dev Phase I

Maps every FR/NFR to source files and automated tests.

| ID | Requirement | Source Files | Tests |
|----|-------------|--------------|-------|
| FR-1.1 | Multi-Sport Taxonomy & Event-Sourced Scoring | `backend/app/domain/sports.py`, `backend/app/api/sports.py`, `backend/app/domain/scoring.py` | `backend/tests/test_sports.py`, `backend/tests/test_scoring.py` |
| FR-1.2 | League & Tournament Setup | `backend/app/domain/leagues.py`, `backend/app/api/leagues.py` | `backend/tests/test_leagues.py` |
| FR-1.3 | Match & Fixture Scheduling | `backend/app/domain/fixtures.py`, `backend/app/api/fixtures.py` | `backend/tests/test_fixtures.py` |
| FR-1.4 | Automated Standings & Tables | `backend/app/domain/standings.py`, `backend/app/api/standings.py` | `backend/tests/test_standings.py` |
| FR-2.1 | Club Profiles & Tenant Isolation | `backend/app/domain/clubs.py`, `backend/app/models/club.py` | `backend/tests/test_clubs.py` |
| FR-2.2 | Roster & Player Registry | `backend/app/domain/roster.py`, `backend/app/api/roster.py` | `backend/tests/test_roster.py` |
| FR-2.3 | Integrated Club Merchandise Store | `backend/app/domain/store.py`, `backend/app/api/store.py` | `backend/tests/test_store.py` |
| FR-5.1 | Five-Tier RBAC | `backend/app/auth/rbac.py`, `backend/app/api/rbac.py` | `backend/tests/test_rbac.py` |
| NFR-3 | Concurrency Correctness | `backend/app/domain/store.py` (SELECT FOR UPDATE SKIP LOCKED) | `backend/tests/test_concurrency.py` |
| NFR-4 | Offline Tolerance | `backend/app/api/offline_sync.py`, `mobile/lib/services/sync_service.dart` | `backend/tests/test_offline_sync.py` |
| NFR-5 | Security | `backend/app/auth/`, rate limiting middleware | `backend/tests/test_security.py` |
| NFR-7 | Reproducibility | `docker-compose.yml`, `backend/app/seed.py` | — |
