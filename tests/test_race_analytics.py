"""Tests for the horse-race form analytics / cover model (race_analytics.py)."""

from __future__ import annotations

import pytest

from a_view_to_a_kill import race_analytics as race


def _two_race_records() -> tuple[race.RaceResult, ...]:
    # Same distance/going/weight; only the normalized time differs, so the
    # EWMA is a clean weighted average of two speed indices.
    return (
        race.RaceResult("Ace", 0, 10.0, "good", 126.0, 135.0),
        race.RaceResult("Ace", 1, 10.0, "good", 126.0, 133.0),
    )


# ---------------------------------------------------------------- validation
@pytest.mark.parametrize("bad", [("", 0, 10.0, "good", 126.0, 135.0), ("  ", 0, 10.0, "good", 126.0, 135.0)])
def test_race_result_rejects_blank_horse(bad: tuple[object, ...]) -> None:
    with pytest.raises(ValueError):
        race.RaceResult(bad[0], bad[1], bad[2], bad[3], bad[4], bad[5])  # type: ignore[arg-type]


def test_race_result_rejects_unknown_going() -> None:
    with pytest.raises(ValueError):
        race.RaceResult("Ace", 0, 10.0, "heavy", 126.0, 135.0)


@pytest.mark.parametrize("distance,weight,time_s", [(0.0, 126.0, 135.0), (10.0, 0.0, 135.0), (10.0, 126.0, 0.0)])
def test_race_result_rejects_nonpositive_fields(distance: float, weight: float, time_s: float) -> None:
    with pytest.raises(ValueError):
        race.RaceResult("Ace", 0, distance, "good", weight, time_s)


# ---------------------------------------------------------------- speed / norm
def test_speed_index_faster_time_is_higher() -> None:
    slow = race.speed_index(race.RaceResult("Ace", 0, 10.0, "good", 126.0, 135.0))
    fast = race.speed_index(race.RaceResult("Ace", 1, 10.0, "good", 126.0, 133.0))
    assert fast > slow


def test_speed_index_identifies_softer_going_as_corrected_faster() -> None:
    # Same raw time on softer going must rate *higher*: the going penalty is
    # subtracted so a slow track's time is brought to firm-equivalent pace.
    soft = race.speed_index(race.RaceResult("Ace", 0, 10.0, "soft", 126.0, 135.0))
    firm = race.speed_index(race.RaceResult("Ace", 1, 10.0, "firm", 126.0, 135.0))
    assert soft > firm


def test_normalize_race_weight_penalty() -> None:
    light = race.normalize_race(race.RaceResult("Ace", 0, 10.0, "good", 126.0, 135.0))
    heavy = race.normalize_race(race.RaceResult("Ace", 1, 10.0, "good", 140.0, 135.0))
    # heavier horse carrying more weight must be normalized faster (less penalized)
    assert heavy < light


# ---------------------------------------------------------------- ratings
def test_form_rating_ewma_two_races() -> None:
    records = _two_race_records()
    ratings = race.form_ratings(records, halflife=1.0)
    s0 = race.speed_index(records[0])
    s1 = race.speed_index(records[1])
    # newest (index 1) weight 0.5^0 = 1; older (index 0) weight 0.5^1 = 0.5
    expected = (1.0 * s1 + 0.5 * s0) / (1.0 + 0.5)
    assert ratings["Ace"].rating == pytest.approx(expected)
    assert ratings["Ace"].races == 2


def test_form_rating_orders_horses_by_performance() -> None:
    ratings = race.form_ratings(race.FORM_TABLE)
    assert ratings["Silverado"].rating > ratings["Bluegrass"].rating


def test_form_rating_empty_raises() -> None:
    with pytest.raises(ValueError):
        race.form_ratings(())


@pytest.mark.parametrize("halflife", [0.0, -1.0])
def test_form_rating_rejects_bad_halflife(halflife: float) -> None:
    with pytest.raises(ValueError):
        race.form_ratings(_two_race_records(), halflife=halflife)


# ---------------------------------------------------------------- probabilities
def test_win_probabilities_sum_to_one_and_in_unit_interval() -> None:
    ratings = race.form_ratings(race.FORM_TABLE)
    probs = race.win_probabilities(ratings)
    values = list(probs.values())
    assert all(0.0 < p < 1.0 for p in values)
    assert sum(values) == pytest.approx(1.0)


def test_win_probabilities_empty_raises() -> None:
    with pytest.raises(ValueError):
        race.win_probabilities({})


def test_win_probabilities_rejects_bad_temperature() -> None:
    with pytest.raises(ValueError):
        race.win_probabilities({"a": 1.0, "b": 2.0}, temperature=0.0)


def test_win_probabilities_higher_rating_better_odds() -> None:
    probs = race.win_probabilities({"a": 5.0, "b": 1.0})
    assert probs["a"] > probs["b"]


def test_expected_order_sorted_descending() -> None:
    ratings = {name: hr.rating for name, hr in race.form_ratings(race.FORM_TABLE).items()}
    order = race.expected_order(ratings)
    values = [v for _, v in order]
    assert values == sorted(values, reverse=True)


# ---------------------------------------------------------------- cover / manipulation
def test_manipulated_probabilities_boosts_target() -> None:
    ratings = {name: hr.rating for name, hr in race.form_ratings(race.FORM_TABLE).items()}
    base = race.win_probabilities(ratings)
    boosted = race.manipulated_probabilities(ratings, "Pegasus", 0.5)
    assert boosted["Pegasus"] > base["Pegasus"]


def test_manipulated_probabilities_unknown_horse_raises() -> None:
    with pytest.raises(ValueError):
        race.manipulated_probabilities({"a": 1.0, "b": 2.0}, "ghost", 0.5)


def test_manipulated_probabilities_negative_boost_raises() -> None:
    with pytest.raises(ValueError):
        race.manipulated_probabilities({"a": 1.0, "b": 2.0}, "a", -0.5)


def test_detection_risk_monotone_in_boost() -> None:
    small = race.detection_risk(race.FORM_TABLE, "Pegasus", 0.1, 0.5)
    large = race.detection_risk(race.FORM_TABLE, "Pegasus", 1.5, 0.5)
    assert 0.0 <= small <= large <= 1.0


def test_detection_risk_zero_boost_is_low() -> None:
    risk = race.detection_risk(race.FORM_TABLE, "Pegasus", 0.0, 0.5)
    # z = (0 - 1.0) / (0.5/sqrt(4)) = -4 -> CDF ~ 3e-5: a no-op boost is invisible.
    assert risk < 0.001


def test_detection_risk_saturates_toward_one_at_high_boost() -> None:
    risk = race.detection_risk(race.FORM_TABLE, "Pegasus", 3.0, 0.5)
    assert risk > 0.999


def test_detection_risk_respects_threshold() -> None:
    # Boost exactly at the threshold -> risk = CDF(0) = 0.5
    risk = race.detection_risk(race.FORM_TABLE, "Pegasus", 1.0, 0.5)
    assert risk == pytest.approx(0.5)


def test_detection_risk_unknown_horse_raises() -> None:
    with pytest.raises(ValueError):
        race.detection_risk(race.FORM_TABLE, "ghost", 0.5, 0.5)


@pytest.mark.parametrize("sigma", [0.0, -1.0])
def test_detection_risk_rejects_bad_sigma(sigma: float) -> None:
    with pytest.raises(ValueError):
        race.detection_risk(race.FORM_TABLE, "Pegasus", 0.5, sigma)  # type: ignore[arg-type]


def test_detection_risk_empty_records_raises() -> None:
    with pytest.raises(ValueError):
        race.detection_risk((), "Pegasus", 0.5, 0.5)


def test_cover_viability_produces_all_keys_and_formula() -> None:
    ratings = {name: hr.rating for name, hr in race.form_ratings(race.FORM_TABLE).items()}
    cover = race.cover_viability(ratings, race.FORM_TABLE, "Pegasus", 0.2, 0.5)
    assert set(cover) == {"win_delta", "detection_risk", "expected_value"}
    assert cover["expected_value"] == pytest.approx(
        cover["win_delta"] * race.PURSE - cover["detection_risk"] * race.DETECTION_PENALTY
    )


def test_cover_expected_value_peaks_at_moderate_boost() -> None:
    ratings = {name: hr.rating for name, hr in race.form_ratings(race.FORM_TABLE).items()}
    modest = race.cover_viability(ratings, race.FORM_TABLE, "Pegasus", 0.05, 0.5)["expected_value"]
    extreme = race.cover_viability(ratings, race.FORM_TABLE, "Pegasus", 3.0, 0.5)["expected_value"]
    assert modest > extreme


def test_cover_expected_value_positive_at_moderate_boost() -> None:
    """A subtle cover is viable; an extreme cheat is not."""
    ratings = {name: hr.rating for name, hr in race.form_ratings(race.FORM_TABLE).items()}
    subtle = race.cover_viability(ratings, race.FORM_TABLE, "Pegasus", 0.2, 0.5)["expected_value"]
    blatant = race.cover_viability(ratings, race.FORM_TABLE, "Pegasus", 3.0, 0.5)["expected_value"]
    assert subtle > 0.0
    assert blatant < 0.0
