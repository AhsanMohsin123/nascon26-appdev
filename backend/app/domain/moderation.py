"""Automated chat moderation (leetspeak/profanity masking, flood detection) & DLQ inspection (Section 5.8)."""
import re
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.domain.signing import sign_day2

_LEET_MAP = str.maketrans({"@": "a", "0": "o", "1": "i", "!": "i", "3": "e", "$": "s"})
_STRIP_CHARS = re.compile(r"[._\-*]")

_PROFANITY = ["badword", "bad word", "porn", "scam", "fuck", "shit", "bitch", "asshole", "idiot spam"]

_FLOOD_RE = re.compile(r"(.)\1{3,}|[!?]{3,}", re.IGNORECASE)


def _normalize(text_: str) -> str:
    lowered = text_.lower().translate(_LEET_MAP)
    return _STRIP_CHARS.sub("", lowered)


def _find_profanity_spans(original: str) -> list[tuple[int, int]]:
    """Finds character spans in the ORIGINAL text whose normalized form matches a profanity token."""
    norm = _normalize(original)
    spans = []
    # Build a mapping from normalized-string index back to original-string index by
    # walking the original string once, since normalization only lowercases/substitutes
    # single chars or strips separator chars (never reorders).
    orig_idx_for_norm_idx = []
    for idx, ch in enumerate(original):
        if _STRIP_CHARS.match(ch):
            continue
        orig_idx_for_norm_idx.append(idx)

    for token in _PROFANITY:
        token_norm = token.replace(" ", "")
        start = 0
        while True:
            pos = norm.find(token_norm, start)
            if pos == -1:
                break
            if pos < len(orig_idx_for_norm_idx) and (pos + len(token_norm) - 1) < len(orig_idx_for_norm_idx):
                orig_start = orig_idx_for_norm_idx[pos]
                orig_end = orig_idx_for_norm_idx[pos + len(token_norm) - 1] + 1
                spans.append((orig_start, orig_end))
            start = pos + 1
    spans.sort()
    merged = []
    for s, e in spans:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    return merged


def _mask(original: str, spans: list[tuple[int, int]]) -> str:
    if not spans:
        return original
    out = []
    last = 0
    for s, e in spans:
        out.append(original[last:s])
        out.append("***")
        last = e
    out.append(original[last:])
    return "".join(out)


def filter_message(text_: str) -> dict:
    """Returns {kind: clean|profanity|flood, text, reason}."""
    if _FLOOD_RE.search(text_):
        return {"kind": "flood", "text": text_, "reason": "flood_character_repeat"}
    spans = _find_profanity_spans(text_)
    if spans:
        return {"kind": "profanity", "text": _mask(text_, spans), "reason": "profanity_leetspeak"}
    return {"kind": "clean", "text": text_, "reason": None}


async def run_moderation_test(db: AsyncSession, body: dict) -> dict:
    chat_room_id = body.get("chat_room_id")
    incoming = body.get("incoming_messages", [])
    check_dlq = body.get("check_dlq", False)
    simulate_failed = int(body.get("simulate_failed_notifications", 0) or 0)

    filtered_messages = []
    kicked_users = []
    muted_users = []

    for msg in incoming:
        result = filter_message(msg.get("text", ""))
        sender = msg.get("sender")
        if result["kind"] == "flood":
            if sender not in muted_users:
                muted_users.append(sender)
            continue  # dropped entirely, never broadcast
        flagged = result["kind"] == "profanity"
        if flagged and sender not in kicked_users:
            kicked_users.append(sender)
        filtered_messages.append({
            "message_id": msg.get("message_id"),
            "sender": sender,
            "text": result["text"],
            "flagged": flagged,
            "reason": result["reason"],
        })

    if simulate_failed > 0:
        for i in range(simulate_failed):
            await db.execute(text(
                "INSERT INTO dlq_events (id, event_type, payload) VALUES (:id, 'notification_failure', :payload)"
            ), {"id": f"dlq-{chat_room_id}-{i}-{_rand_suffix()}", "payload": json.dumps({"chat_room_id": chat_room_id})})
        await db.commit()

    dlq_rows = (await db.execute(text("SELECT id, event_type, payload FROM dlq_events"))).fetchall()
    queue_depth = len(dlq_rows)
    undelivered_events = [{"id": r[0], "type": r[1]} for r in dlq_rows] if check_dlq else []

    await db.execute(text(
        "INSERT INTO moderation_actions (chat_room_id, kicked_users, muted_users) VALUES (:id, :k, :m) "
        "ON CONFLICT (chat_room_id) DO UPDATE SET kicked_users=:k, muted_users=:m"
    ), {"id": chat_room_id, "k": json.dumps(kicked_users), "m": json.dumps(muted_users)})
    await db.commit()

    sig_payload = {
        "chat_room_id": chat_room_id, "flagged_count": sum(1 for m in filtered_messages if m["flagged"]),
        "kicked_users": kicked_users, "queue_depth": queue_depth,
    }

    return {
        "chat_room_id": chat_room_id,
        "filtered_messages": filtered_messages,
        "kicked_users": kicked_users,
        "muted_users": muted_users,
        "dlq_status": {"queue_depth": queue_depth, "undelivered_events": undelivered_events},
        "signature": sign_day2(chat_room_id, sig_payload),
    }


def _rand_suffix() -> str:
    import uuid
    return uuid.uuid4().hex[:8]
