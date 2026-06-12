"""Unit tests for the Elo engine, bracket config, and simulation helpers."""
import numpy as np
import pytest

from cupcast import config
from cupcast.elo import EloEngine, expected_score, goal_multiplier, k_factor
from cupcast.simulate import assign_thirds, sample_score


def test_expected_score_symmetry():
    assert expected_score(1500, 1500) == pytest.approx(0.5)
    assert expected_score(1600, 1400) + expected_score(1400, 1600) == pytest.approx(1.0)
    assert expected_score(1900, 1500) > 0.9


def test_goal_multiplier():
    assert goal_multiplier(0) == 1.0
    assert goal_multiplier(1) == 1.0
    assert goal_multiplier(2) == 1.5
    assert goal_multiplier(3) == pytest.approx(14 / 8)
    assert goal_multiplier(-3) == goal_multiplier(3)


def test_k_factor_ordering():
    assert k_factor("FIFA World Cup") > k_factor("FIFA World Cup qualification") \
           > k_factor("Friendly")


def test_elo_zero_sum_and_direction():
    eng = EloEngine()
    eng.rate_match("A", "B", 3, 0, "Friendly", neutral=True)
    assert eng.ratings["A"] > config.ELO_START > eng.ratings["B"]
    assert eng.ratings["A"] + eng.ratings["B"] == pytest.approx(2 * config.ELO_START)


def test_home_advantage_dampens_home_win_gain():
    neutral, home = EloEngine(), EloEngine()
    neutral.rate_match("A", "B", 1, 0, "Friendly", neutral=True)
    home.rate_match("A", "B", 1, 0, "Friendly", neutral=False)
    assert home.ratings["A"] < neutral.ratings["A"]  # expected to win at home


def test_draw_structure():
    assert len(config.WC_TEAMS) == 48
    assert len(set(config.WC_TEAMS)) == 48
    assert len(config.GROUPS) == 12
    assert all(len(t) == 4 for t in config.GROUPS.values())
    assert config.HOSTS <= set(config.WC_TEAMS)


def test_bracket_slots_consistent():
    slots = [s for pair in config.R32.values() for s in pair]
    winners = [s for s in slots if s.startswith("1")]
    runners = [s for s in slots if s.startswith("2")]
    thirds = [s for s in slots if s.startswith("3:")]
    assert sorted(winners) == sorted(f"1{g}" for g in config.GROUPS)
    assert sorted(runners) == sorted(f"2{g}" for g in config.GROUPS)
    assert len(thirds) == 8
    fed = [m for pair in config.R16.values() for m in pair]
    assert sorted(fed) == sorted(config.R32)  # every R32 winner feeds exactly one R16 tie


def test_sample_score_respects_outcome():
    rng = np.random.default_rng(0)
    for outcome, check in [(0, lambda h, a: h > a), (1, lambda h, a: h == a),
                           (2, lambda h, a: h < a)]:
        p = np.zeros(3)
        p[outcome] = 1.0
        for _ in range(50):
            gh, ga = sample_score(p, (1.4, 1.1), rng)
            assert check(gh, ga)


def test_match_detail_consistency():
    """Scoreline grid must agree with the calibrated W/D/L probabilities."""
    pytest.importorskip("scipy")
    from cupcast.predict import Predictor
    if not (config.MODELS_DIR / "model.joblib").exists():
        pytest.skip("model artifacts not trained")
    d = Predictor().match_detail("Brazil", "Morocco", neutral=True)
    m = d["markets"]
    assert 0.99 < d["p_home"] + d["p_draw"] + d["p_away"] < 1.01
    top = sum(s["p"] for s in d["top_scorelines"])
    assert 0 < top <= 1
    assert m["over_1_5"] > m["over_2_5"] > m["over_3_5"]
    assert m["win_to_nil_home"] <= m["clean_sheet_home"] <= 1
    # BTTS and both-clean-sheet-ish events partition sensibly
    assert m["btts"] + m["clean_sheet_home"] + m["clean_sheet_away"] >= 0.99


def test_assign_thirds_respects_pools():
    rng = np.random.default_rng(1)
    # thirds from groups A,B,C,D,E,F,G,H (a combination with a valid matching)
    qualified = [config.GROUPS[g][2] for g in "ABCDEFGH"]
    assignment = assign_thirds(qualified, rng)
    assert len(assignment) == 8
    assert len(set(assignment.values())) == 8
    for match, team in assignment.items():
        pool = config.R32[match][1].split(":")[1]
        assert config.TEAM_GROUP[team] in pool
