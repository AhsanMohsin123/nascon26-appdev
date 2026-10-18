"""DAY2_SALT HMAC-SHA256 signing — exact recipe from Day 2 spec Section 5.3 / Appendix A."""
import hmac
import hashlib
import json

from app.config import settings


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sign_day2(entity_id: str, sig_payload: dict) -> str:
    msg = (entity_id + "|" + canonical(sig_payload)).encode("utf-8")
    return hmac.new(settings.day2_salt.encode("utf-8"), msg, hashlib.sha256).hexdigest()
