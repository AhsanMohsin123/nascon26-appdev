import pytest
from app.domain.fixtures import _circle_method, _seed_order, _round_robin, _swiss, _single_elim


def test_round_robin_even_teams():
    result = _round_robin(["t1", "t2", "t3", "t4"], {})
    assert result["round_count"] == 3
    assert result["team_count"] == 4
    for r in result["rounds"]:
        assert len(r["matches"]) == 2
        assert r["byes"] == []


def test_round_robin_odd_teams():
    result = _round_robin(["t1", "t2", "t3"], {})
    assert result["round_count"] == 3
    for r in result["rounds"]:
        assert len(r["byes"]) == 1


def test_round_robin_double_leg():
    result = _round_robin(["t1", "t2", "t3", "t4"], {"legs": 2})
    assert result["round_count"] == 6
    assert result["legs"] == 2


def test_seed_order_8():
    order = _seed_order(8)
    assert order == [1, 8, 4, 5, 2, 7, 3, 6]


def test_single_elim_6_teams():
    result = _single_elim(["t1", "t2", "t3", "t4", "t5", "t6"], {})
    assert result["bracket_size"] == 8
    r1 = result["rounds"][0]["matches"]
    # R1M1 should be bye (seed 8 missing)
    assert r1[0]["bye"] is True
    assert r1[0]["home"] == "t1"


def test_swiss_round1_exact():
    result = _swiss(["t1", "t2", "t3", "t4", "t5"], {"total_rounds": 3, "round": 1, "history": []})
    assert result["bye"] == "t5"  # last seed gets bye when odd
    assert len(result["pairings"]) == 2
