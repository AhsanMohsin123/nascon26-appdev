# Architecture Decision Records — NaSCon '26 Phase II

Each record states the decision, why we made it, and the trade-off, pointing at the code that implements it.

## ADR-01 — Async FastAPI + PostgreSQL 16
**Decision:** Python FastAPI with async SQLAlchemy/asyncpg on PostgreSQL 16 (`backend/app/main.py`, `backend/app/database.py`).
**Why:** Non-blocking I/O lets one process serve many concurrent guest viewers and scoring writes; Postgres gives transactional row locks for inventory and merges.
**Trade-off:** Raw SQL via `text()` in domain services is explicit but more verbose than an ORM-only layer.

## ADR-02 — HMAC-SHA256 signing with DAY2_SALT and canonical JSON
**Decision:** `signature = HMAC-SHA256(DAY2_SALT, entity_id + "|" + json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False))` (`backend/app/domain/signing.py`).
**Why:** Deterministic bytes make signatures reproducible by the grader; the salt is read only from the environment, never committed.
**Trade-off:** Any field added to a signed payload changes the signature, so payload shape is frozen per endpoint (Section 5.3).

## ADR-03 — Event-sourced scoring
**Decision:** Scores are rebuilt from the append-only `match_events` log; corrections are compensating events (`backend/app/domain/scoring.py`).
**Why:** Full audit trail and idempotent replays by `event_id`; QR routes and standings derive from current state with no cached copies to drift.
**Trade-off:** Reads recompute from the log; acceptable at competition scale.

## ADR-04 — Server-enforced guest write boundary
**Decision:** `reject_guest_write()` (`backend/app/auth/middleware.py`) returns `403 GUEST_WRITE_FORBIDDEN` for any `guest_anon_tok_*` bearer on `/api/v1/chat`, `/audit/v1/checkout`, `/audit/v1/events`.
**Why:** Hiding buttons in the UI gives zero security; the spec voids credit for client-only enforcement.
**Trade-off:** Each write route must opt in to the guard explicitly.

## ADR-05 — Row-locked inventory reservation
**Decision:** Checkout reserves stock with `SELECT ... FOR UPDATE` inside one transaction (`backend/app/domain/store.py`); cart merge checks merged quantity against stock before writing (`backend/app/domain/guest_cart.py`).
**Why:** Prevents overselling under concurrent checkouts.
**Trade-off:** Hot variants serialize on their row lock.

## ADR-06 — Deterministic co-stream host handoff
**Decision:** On host drop, the host is removed and `participants[1]` (first remaining, array order) becomes `active_host`; a sole host terminates the session (`backend/app/domain/costream.py`). `chat_room_id` and `composite_playback_url` are derived from `session_id`, so they survive handoff.
**Why:** Same input always yields the same state, which makes the result testable and signable.
**Trade-off:** No real media/SFU process yet, so "zero zombie processes" holds trivially.

## ADR-07 — Normalized moderation
**Decision:** Normalize leetspeak (`@→a, 0→o, 1/!→i, 3→e, $→s`, strip `_ . - *`), match a profanity dictionary, map matches back to original character spans and mask with `***`; messages with 4+ repeated characters or `!!!`/`???` are dropped and the sender muted (`backend/app/domain/moderation.py`).
**Why:** Catches obfuscated words while preserving the rest of the message verbatim, as the spec example requires.
**Trade-off:** Dictionary-based, so unseen variants pass through.

## ADR-08 — Privacy-safe QR telemetry and erasure
**Decision:** Scan telemetry stores only aggregate counts per `(entity_id, device_family, UTC hour bucket)`; no IP, raw User-Agent or cookies (`backend/app/domain/qr.py`). `DELETE /audit/v1/privacy/user/{id}` anonymizes the user row and unlinks guest tokens (`backend/app/domain/observability.py`).
**Why:** NFR-9 data minimization; the short URL stays constant while the target route is computed from live match state at scan time.
**Trade-off:** Aggregates can't be broken down per visitor.

## Known gaps (honest status at code freeze)
- No real RTMP/WHIP ingest, HLS playback or SFU composition; stream and co-stream endpoints implement the contract only.
- No WebSocket/SSE server; the mobile app polls scores every 3 s for update banners.
- Selenium, Appium and k6 suites exist but have not been executed; only `tests/reports/backend-report.xml` (47 passed) is a real run.
- Phase II module line coverage is 36–93% (see `COVERAGE_DAY2.json`), below the 85% target.
