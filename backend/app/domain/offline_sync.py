"""Offline sync — replay queued device actions with conflict resolution."""
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.domain import scoring, roster as roster_svc


async def process(db: AsyncSession, body: dict) -> dict:
    device_id = body.get("device_id")
    actions = body.get("actions", [])

    if not actions or len(actions) > 100:
        raise HTTPException(400, {"error": {"code": "VALIDATION_ERROR", "message": "actions must be 1-100 items.", "details": {"fields": ["actions"]}}})

    sorted_actions = sorted(actions, key=lambda a: (a.get("queued_at", ""), actions.index(a)))

    results = []
    applied = rejected = duplicate = 0

    for proc_order, action in enumerate(sorted_actions, 1):
        action_id = action.get("action_id")
        action_type = action.get("type")
        base_version = action.get("base_version", 0)
        payload = action.get("payload", {})

        existing = await db.execute(text("SELECT id FROM offline_sync_actions WHERE device_id = :did AND action_id = :aid"), {"did": device_id, "aid": action_id})
        if existing.fetchone():
            results.append({"action_id": action_id, "status": "duplicate", "resolution": "skipped_duplicate", "error_code": None, "processed_order": proc_order, "server_version": base_version, "signature": None})
            duplicate += 1
            continue

        try:
            if action_type == "score_event":
                match_id = payload.get("match_id")
                current_ver_row = await db.execute(text("SELECT COUNT(*) FROM match_events WHERE match_id = :mid"), {"mid": match_id})
                current_ver = current_ver_row.scalar() or 0

                if base_version > current_ver:
                    raise Exception("INVALID_BASE_VERSION")

                result = await scoring.append_event(db, payload)
                resolution = "appended" if base_version == current_ver else "rebased_append"
                results.append({"action_id": action_id, "status": "applied", "resolution": resolution, "error_code": None, "processed_order": proc_order, "server_version": result["sequence"], "signature": result["signature"]})
                applied += 1

            elif action_type == "roster_transfer":
                player_id = payload.get("player_id")
                current_ver_row = await db.execute(text("SELECT COUNT(*) FROM roster_audit WHERE player_id = :pid"), {"pid": player_id})
                current_ver = current_ver_row.scalar() or 0

                if base_version > current_ver:
                    raise Exception("INVALID_BASE_VERSION")

                result = await roster_svc.transfer(db, payload)
                results.append({"action_id": action_id, "status": "applied", "resolution": "appended", "error_code": None, "processed_order": proc_order, "server_version": current_ver + 1, "signature": None})
                applied += 1

        except HTTPException as e:
            err_body = e.detail if isinstance(e.detail, dict) else {}
            code = err_body.get("error", {}).get("code", "UNKNOWN_ERROR")
            results.append({"action_id": action_id, "status": "rejected", "resolution": "server_wins", "error_code": code, "processed_order": proc_order, "server_version": base_version, "signature": None})
            rejected += 1
        except Exception as ex:
            code = str(ex) if str(ex) in ("INVALID_BASE_VERSION",) else "UNKNOWN_ERROR"
            results.append({"action_id": action_id, "status": "rejected", "resolution": "server_wins", "error_code": code, "processed_order": proc_order, "server_version": base_version, "signature": None})
            rejected += 1

        await db.execute(text(
            "INSERT INTO offline_sync_actions (device_id, action_id) VALUES (:did, :aid) ON CONFLICT DO NOTHING"
        ), {"did": device_id, "aid": action_id})
        await db.commit()

    original_order = {a["action_id"]: a for a in actions}
    final_results = sorted(results, key=lambda r: list(original_order.keys()).index(r["action_id"]))

    return {"device_id": device_id, "results": final_results, "summary": {"applied": applied, "rejected": rejected, "duplicate": duplicate}}
