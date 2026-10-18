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
| FR-3.1 | `streaming` | Public Athlete Identity & Social Graph | — | — | NOT STARTED |
| FR-3.2 | `streaming` | Stream Key Lifecycle (generate/rotate/revoke) | `backend/app/api/streaming.py`, `backend/app/domain/streaming.py` | `backend/tests/test_streaming.py` (8 tests) | PASS — live-verified against running stack + Appendix A vector format |
| FR-3.2 | `streaming` | Actual WebRTC/RTMP ingest, HLS playback, overlays | `docker-compose.yml` (media-server service only, MediaMTX) | — | NOT STARTED — contract endpoints exist, real media pipeline integration does not |
| FR-3.3 | `costream` | Synchronized 4-Way Co-Streaming & Host Handoff | `backend/app/api/costream.py`, `backend/app/domain/costream.py` | `backend/tests/test_phase2_contracts.py` (6 tests) | PASS — handoff, termination, capacity, layout validation all live-verified |
| FR-4.1 | `qr_guest` | Dynamic Cryptographic QR Deep-Linking & Exports | `backend/app/api/qr.py`, `backend/app/domain/qr.py` | `backend/tests/test_qr.py` (9 tests) | PASS — incl. dynamic target mutation after match state change, SVG/PNG/PDF export |
| FR-4.2 | `qr_guest` | Zero-Account Guest Experience | `backend/app/api/guest.py` (anonymous token issuance), Guest Web Player `/web/*` | `tests/selenium/test_guest_grid.py` | NOT STARTED — Guest Web Player HTML/DOM not built, Selenium suite will fail until it exists |
| FR-4.3 | `qr_guest` | Server-Enforced Read-Only Boundary (HTTP 403) | `backend/app/auth/middleware.py` (`reject_guest_write`) | `backend/tests/test_phase2_contracts.py::test_guest_token_blocked_on_direct_writes` | PASS — verified on `/api/v1/chat`, `/audit/v1/checkout`, `/audit/v1/events` |
| FR-4.4 | `qr_guest` | Progressive Registration & Atomic Cart Merge | `backend/app/domain/guest_cart.py`, `backend/app/api/guest.py` | `backend/tests/test_phase2_contracts.py` (3 tests) | PASS — idempotent replay, already-merged conflict, atomic merge all live-verified |
| FR-5.2 | `moderation_dlq`| Notification Bus & Dead-Letter Queue (DLQ) | `backend/app/domain/moderation.py` (DLQ inspection only) | `backend/tests/test_phase2_contracts.py::test_dlq_depth_from_simulated_failures` | PARTIAL — DLQ depth/inspection works; real retry/WebSocket dispatch not built |
| FR-5.3 | `moderation_dlq`| Automated Chat Moderation (Leetspeak/Flood) | `backend/app/domain/moderation.py`, `backend/app/api/moderation.py` | `backend/tests/test_phase2_contracts.py::test_moderation_spec_example` | PASS — matches spec's worked example byte-for-byte, verified under 10x concurrent race |
| NFR-1 | — | Real-Time Score Latency (<500ms p95, WebSocket) | — | — | NOT STARTED — no WebSocket/SSE server exists |
| NFR-2 | — | High-Concurrency Scale (550 VUs) | `tests/k6_load.js` | — | NOT TESTED — script present (matches spec exactly), never actually run against this stack |
| NFR-6 | `observability` | System Observability (Prometheus /metrics) | `backend/app/api/observability.py`, `backend/app/domain/observability.py` | `backend/tests/test_phase2_contracts.py::test_metrics_*` | PASS — real counts from DB (active streams, DLQ depth, QR scans); ws_connections/bitrate hardcoded 0 (no real tracking yet) |
| NFR-8 | — | Guest Web Accessibility (WCAG 2.1 AA) | — | — | NOT STARTED — depends on Guest Web Player |
| NFR-9 | `observability` | Privacy & Data Minimization (Right to Erasure) | `backend/app/domain/observability.py::erase_user` | `backend/tests/test_phase2_contracts.py::test_privacy_erasure*` | PASS |
