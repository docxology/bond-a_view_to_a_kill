"""Horse-race form analytics — cover-operation modeling.

ZORIN runs a racing stable as cover for his silicon-valley operation: the
winning horse keeps eyes (and capital) away from the mine. This module
implements both sides of that cover:

* **Legitimate form analytics** — turn raw race records into ratings and
  win probabilities: normalized speed indices (corrected for distance,
  going, and weight), an exponentially-weighted-moving-average form rating
  per horse, and a softmax win-probability model.
* **Cover (manipulation) risk model** — given a performance boost applied to
  one horse, estimate the increase in its win probability and the
  probability the scheme is *detected* (a deterministic signal-detection
  model: an improvement large relative to the horse's natural race-to-race
  variance is suspicious). ``cover_viability`` combines the two into an
  expected-value score.

All of it is pure, deterministic math (stdlib + numpy, no randomness, no
``bond_api``). The default form table is a documented reconstruction of a
mid-1980s Epsom-style flat-race card; race times are fixed model parameters
for reproducibility (annotated as model data in the claim ledger).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

__all__ = [
    "RaceResult",
    "HorseRating",
    "GOING_CORRECTION",
    "PAR_SECONDS_PER_FURLONG",
    "PURSE",
    "DETECTION_PENALTY",
    "FORM_TABLE",
    "normalize_race",
    "speed_index",
    "form_ratings",
    "win_probabilities",
    "expected_order",
    "manipulated_probabilities",
    "detection_risk",
    "cover_viability",
]

#: Going-track correction, in seconds per furlong, added to raw time.
#: Firmer going is faster (smaller correction).
GOING_CORRECTION = {"firm": 0.0, "good": 0.3, "soft": 0.7}

#: Base weight (lbs) below which no weight penalty is applied.
BASE_WEIGHT = 126.0

#: Weight adjustment: seconds per furlong per pound above the base weight.
WEIGHT_SECONDS_PER_LB = 0.02

#: Par speed benchmark, in seconds per furlong, used to build speed indices.
PAR_SECONDS_PER_FURLONG = 14.0

#: Prize money the operation stands to win, and the penalty if detected.
PURSE = 100_000.0
DETECTION_PENALTY = 900_000.0

#: Signal-detection threshold (speed-index units): a horse whose performance
#: improves by more than this above its own baseline is flagged by the
#: stewards. Bigger threshold = more lenient (harder to detect a cheat).
DETECTION_THRESHOLD = 1.0


@dataclass(frozen=True)
class RaceResult:
    """One horse's finish in one race (a single form record)."""

    horse: str
    race_index: int  # chronological order of the race (0 = oldest)
    distance: float  # furlongs
    going: str  # firm | good | soft
    weight: float  # lbs carried
    time_s: float  # raw finish time, seconds

    def __post_init__(self) -> None:
        if not isinstance(self.horse, str) or not self.horse.strip():
            raise ValueError("RaceResult.horse must be a non-empty string")
        if not isinstance(self.race_index, int) or isinstance(self.race_index, bool):
            raise ValueError("RaceResult.race_index must be an integer")
        if self.race_index < 0:
            raise ValueError("RaceResult.race_index must be non-negative")
        for label, value in (
            ("distance", self.distance),
            ("weight", self.weight),
            ("time_s", self.time_s),
        ):
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ValueError(f"RaceResult.{label} must be a number")
        if self.distance <= 0:
            raise ValueError("RaceResult.distance must be positive")
        if self.weight <= 0:
            raise ValueError("RaceResult.weight must be positive")
        if self.time_s <= 0:
            raise ValueError("RaceResult.time_s must be positive")
        if self.going not in GOING_CORRECTION:
            raise ValueError(f"unknown going {self.going!r}; expected one of {sorted(GOING_CORRECTION)}")


@dataclass(frozen=True)
class HorseRating:
    """A horse's aggregate form rating across its recorded races."""

    horse: str
    rating: float
    races: int


#: Documented mid-1980s Epsom-style flat-race card: 5 horses x 4 races.
#: (Model data — race times are fixed parameters, see claim ledger.)
FORM_TABLE = (
    # ---- Pegasus (ZORIN's cover horse) ----
    RaceResult("Pegasus", 0, 10.0, "good", 126.0, 134.8),
    RaceResult("Pegasus", 1, 12.0, "soft", 128.0, 169.4),
    RaceResult("Pegasus", 2, 8.0, "firm", 125.0, 106.9),
    RaceResult("Pegasus", 3, 10.0, "good", 127.0, 133.9),
    # ---- Thunderbolt ----
    RaceResult("Thunderbolt", 0, 10.0, "good", 127.0, 135.0),
    RaceResult("Thunderbolt", 1, 10.0, "firm", 126.0, 133.7),
    RaceResult("Thunderbolt", 2, 12.0, "good", 129.0, 168.6),
    RaceResult("Thunderbolt", 3, 8.0, "soft", 126.0, 108.8),
    # ---- Silverado ----
    RaceResult("Silverado", 0, 8.0, "firm", 125.0, 106.4),
    RaceResult("Silverado", 1, 10.0, "good", 128.0, 134.6),
    RaceResult("Silverado", 2, 12.0, "good", 126.0, 168.2),
    RaceResult("Silverado", 3, 10.0, "soft", 130.0, 136.0),
    # ---- Bluegrass ----
    RaceResult("Bluegrass", 0, 12.0, "soft", 127.0, 170.1),
    RaceResult("Bluegrass", 1, 10.0, "firm", 125.0, 134.0),
    RaceResult("Bluegrass", 2, 8.0, "good", 126.0, 107.2),
    RaceResult("Bluegrass", 3, 12.0, "good", 127.0, 168.9),
    # ---- Ironclad ----
    RaceResult("Ironclad", 0, 10.0, "firm", 126.0, 134.3),
    RaceResult("Ironclad", 1, 8.0, "good", 125.0, 106.8),
    RaceResult("Ironclad", 2, 10.0, "soft", 129.0, 136.4),
    RaceResult("Ironclad", 3, 12.0, "good", 126.0, 168.7),
)


def normalize_race(record: RaceResult) -> float:
    """Return the normalized seconds-per-furlong pace for one race.

    Raw time is corrected for the going (per furlong) and the weight carried
    (seconds per furlong per pound above the base), then divided by distance.
    """
    going_adj = GOING_CORRECTION[record.going] * record.distance
    weight_adj = max(record.weight - BASE_WEIGHT, 0.0) * WEIGHT_SECONDS_PER_LB * record.distance
    return (record.time_s - going_adj - weight_adj) / record.distance


def speed_index(record: RaceResult) -> float:
    """Speed index: seconds saved per furlong versus par. Higher is faster."""
    return PAR_SECONDS_PER_FURLONG - normalize_race(record)


def form_ratings(
    records: tuple[RaceResult, ...],
    halflife: float = 2.0,
) -> dict[str, HorseRating]:
    """Exponentially-weighted moving-average form rating per horse.

    Recent races weigh more: a race ``age`` races before the newest gets
    weight ``0.5 ** (age / halflife)``. Returns a ``name -> HorseRating``
    mapping, ordered by the first appearance in ``records``.
    """
    if not isinstance(halflife, (int, float)) or isinstance(halflife, bool):
        raise ValueError("halflife must be a number")
    if halflife <= 0:
        raise ValueError("halflife must be positive")
    if not records:
        raise ValueError("records must not be empty")
    order: list[str] = []
    for record in records:
        if record.horse not in order:
            order.append(record.horse)
    by_horse: dict[str, list[RaceResult]] = {name: [] for name in order}
    for record in records:
        by_horse[record.horse].append(record)
    newest = {name: max(r.race_index for r in group) for name, group in by_horse.items()}
    out: dict[str, HorseRating] = {}
    for name in order:
        group = by_horse[name]
        total_weight = 0.0
        weighted_sum = 0.0
        for record in group:
            age = float(newest[name] - record.race_index)
            weight = 0.5 ** (age / halflife)
            total_weight += weight
            weighted_sum += weight * speed_index(record)
        rating = weighted_sum / total_weight if total_weight > 0 else 0.0
        out[name] = HorseRating(horse=name, rating=float(rating), races=len(group))
    return out


def win_probabilities(
    ratings: dict[str, HorseRating] | dict[str, float],
    temperature: float = 1.0,
) -> dict[str, float]:
    """Softmax win probabilities from form ratings.

    ``temperature > 0`` controls spread (lower = more decisive). Probabilities
    are strictly positive and sum to 1.
    """
    if not isinstance(temperature, (int, float)) or isinstance(temperature, bool):
        raise ValueError("temperature must be a number")
    if temperature <= 0:
        raise ValueError("temperature must be positive")
    names = list(ratings.keys())
    if not names:
        raise ValueError("ratings must not be empty")
    values = np.array(
        [r.rating if isinstance(r, HorseRating) else float(r) for r in ratings.values()],
        dtype=float,
    )
    shifted = values - float(np.max(values))
    exp_values = np.exp(shifted / temperature)
    probs = exp_values / float(np.sum(exp_values))
    return {name: float(p) for name, p in zip(names, probs)}


def expected_order(ratings: dict[str, float]) -> list[tuple[str, float]]:
    """Horses ranked by rating, highest first: ``(name, rating)`` pairs."""
    order = sorted(ratings.items(), key=lambda item: (-item[1], item[0]))
    return [(name, float(rating)) for name, rating in order]


def manipulated_probabilities(
    ratings: dict[str, float],
    boosted: str,
    boost: float,
    temperature: float = 1.0,
) -> dict[str, float]:
    """Win probabilities after adding a performance ``boost`` (seconds per
    furlong) to one horse's rating."""
    if boosted not in ratings:
        raise ValueError(f"unknown horse {boosted!r}")
    if not isinstance(boost, (int, float)) or isinstance(boost, bool):
        raise ValueError("boost must be a number")
    if boost < 0:
        raise ValueError("boost must be non-negative")
    adjusted = dict(ratings)
    adjusted[boosted] = adjusted[boosted] + float(boost)
    return win_probabilities(adjusted, temperature)


def detection_risk(
    records: tuple[RaceResult, ...],
    horse: str,
    boost: float,
    natural_sigma: float,
    threshold: float = DETECTION_THRESHOLD,
) -> float:
    """Probability the manipulation is detected (0..1).

    A horse's races have natural race-to-race variability ``natural_sigma``
    (speed-index units), so the standard error of its mean performance over
    ``n`` recent races is ``natural_sigma / sqrt(n)``. The stewards flag a
    horse whose performance looks ``threshold`` speed-index units better than
    its own baseline; the observed improvement is a draw around ``boost``. The
    detection probability is therefore the probability that a normal draw with
    mean ``boost`` and standard error ``natural_sigma / sqrt(n)`` exceeds the
    threshold:

        risk = CDF((boost - threshold) / sigma_eff)

    A boost well below the threshold is essentially invisible; a boost far
    above it is almost certainly caught — exactly the trade-off ``cover_viability``
    needs to score.
    """
    if not records:
        raise ValueError("records must not be empty")
    group = [r for r in records if r.horse == horse]
    if not group:
        raise ValueError(f"no form records for horse {horse!r}")
    if not isinstance(boost, (int, float)) or isinstance(boost, bool):
        raise ValueError("boost must be a number")
    if boost < 0:
        raise ValueError("boost must be non-negative")
    if not isinstance(natural_sigma, (int, float)) or isinstance(natural_sigma, bool):
        raise ValueError("natural_sigma must be a number")
    if natural_sigma <= 0:
        raise ValueError("natural_sigma must be positive")
    if not isinstance(threshold, (int, float)) or isinstance(threshold, bool):
        raise ValueError("threshold must be a number")
    n = len(group)
    sigma_eff = natural_sigma / math.sqrt(n)
    z = (boost - threshold) / sigma_eff
    return _normal_cdf(z)


def cover_viability(
    ratings: dict[str, float],
    records: tuple[RaceResult, ...],
    boosted: str,
    boost: float,
    natural_sigma: float,
    temperature: float = 1.0,
) -> dict[str, float]:
    """Expected-value trade-off of the cover operation for ``boosted``.

    Returns ``win_delta`` (gain in win probability), ``detection_risk``, and
    ``expected_value`` = ``win_delta * PURSE - detection_risk *
    DETECTION_PENALTY``. A too-large boost raises detection risk faster than
    it buys win probability, so expected value peaks at a moderate boost.
    """
    base = win_probabilities(ratings, temperature)
    boosted_probs = manipulated_probabilities(ratings, boosted, boost, temperature)
    win_delta = boosted_probs[boosted] - base[boosted]
    risk = detection_risk(records, boosted, boost, natural_sigma)
    expected_value = win_delta * PURSE - risk * DETECTION_PENALTY
    return {
        "win_delta": float(win_delta),
        "detection_risk": float(risk),
        "expected_value": float(expected_value),
    }


def _normal_cdf(z: float) -> float:
    """Standard-normal CDF via the error function (deterministic)."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
