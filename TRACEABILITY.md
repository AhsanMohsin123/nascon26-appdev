# Traceability Matrix — NaSCon '26 App Dev Phase I & Phase II

Maps every FR/NFR to source files and automated tests.

## Phase I Requirements

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
| NFR-7 | Reproducibility | `docker-compose.yml`, `backend/app/domain/seed.py` | — |

## Phase II Requirements

| ID | Module | Requirement | Source Files | Tests | Status |
|----|--------|-------------|--------------|-------|--------|
| FR-3.1 | `streaming` | Public Athlete Identity & Social Graph | `backend/app/domain/streaming.py` | `backend/tests/test_streaming.py` | PARTIAL |
| FR-3.2 | `streaming` | Low-Latency Solo Streaming & Dynamic Overlays | `backend/app/api/streaming.py`, `backend/app/domain/streaming.py` | `backend/tests/test_streaming.py` | PASS |
| FR-3.3 | `costream` | Synchronized 4-Way Co-Streaming & Host Handoff | `backend/app/api/costream.py`, `backend/app/domain/costream.py` | `backend/tests/test_costream.py` | PARTIAL |
| FR-4.1 | `qr_guest` | Dynamic Cryptographic QR Deep-Linking & Exports | `backend/app/api/qr.py`, `backend/app/domain/qr.py` | `backend/tests/test_qr.py` | PASS |
| FR-4.2 | `qr_guest` | Zero-Account Guest Experience | `backend/app/api/guest.py`, Guest Web Player `/web/*` | `tests/selenium/test_guest_grid.py` | PARTIAL |
| FR-4.3 | `qr_guest` | Server-Enforced Read-Only Boundary (HTTP 403) | `backend/app/auth/guest_guard.py` | `backend/tests/test_guest.py` | PARTIAL |
| FR-4.4 | `qr_guest` | Progressive Registration & Atomic Cart Merge | `backend/app/domain/cart_merge.py` | `backend/tests/test_cart_merge.py` | PARTIAL |
| FR-5.2 | `moderation_dlq`| Notification Bus & Dead-Letter Queue (DLQ) | `backend/app/domain/notifications.py` | `backend/tests/test_dlq.py` | PARTIAL |
| FR-5.3 | `moderation_dlq`| Automated Chat Moderation (Leetspeak/Flood) | `backend/app/domain/moderation.py` | `backend/tests/test_moderation.py` | PARTIAL |
| NFR-1 | `observability` | Real-Time Score Latency (<500ms p95) | `backend/app/api/events.py` | `backend/tests/test_events_ws.py` | PASS |
| NFR-2 | `observability` | High-Concurrency Scale (550 VUs) | `docker-compose.yml`, FastAPI pool | `tests/k6_load.js` | PASS |
| NFR-6 | `observability` | System Observability (Prometheus /metrics) | `backend/app/api/metrics.py` | `backend/tests/test_metrics.py` | PARTIAL |
| NFR-8 | `qr_guest` | Guest Web Accessibility (WCAG 2.1 AA) | Guest Web Player DOM contract | `tests/selenium/test_guest_grid.py` | PARTIAL |
| NFR-9 | `observability` | Privacy & Data Minimization (Right to Erasure) | `backend/app/api/privacy.py` | `backend/tests/test_privacy.py` | PARTIAL |
