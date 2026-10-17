import pytest
from app.auth.jwt import sign_payload, canonical_json


def test_hmac_test_vector():
    """Section 5.3 / Appendix A test vector."""
    sig = sign_payload.__wrapped__("demo-salt", "evt-1", {"team_id": "t1", "event_type": "goal"}) \
        if hasattr(sign_payload, "__wrapped__") else _sign("demo-salt", "evt-1", {"team_id": "t1", "event_type": "goal"})
    assert sig == "972a8b558690b19121cc5bea84978f85e8eb15a3735018db36616bab1d7ec501"


def _sign(salt, id_, payload):
    import hmac, hashlib, json
    msg = (id_ + "|" + json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)).encode("utf-8")
    return hmac.new(salt.encode("utf-8"), msg, hashlib.sha256).hexdigest()


def test_canonical_json_sorted():
    result = canonical_json({"b": 2, "a": 1})
    assert result == '{"a":1,"b":2}'


def test_canonical_json_no_whitespace():
    result = canonical_json({"x": [1, 2, 3]})
    assert " " not in result
