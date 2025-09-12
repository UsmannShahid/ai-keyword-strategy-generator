"""
Unified opportunity scoring utilities (0–100 scale) used across API paths.

Centralizes the multi-factor scorer so services and core code use the same logic
and thresholds, ensuring consistent quick-win selection and UI alignment.
"""
from dataclasses import dataclass
from typing import Dict, Tuple, Optional, Union
import math

DifficultyMode = str  # "easy" | "medium" | "hard"


@dataclass(frozen=True)
class MultiFactorParams:
    # Volume scoring
    volume_log_base: float = 10.0
    volume_max_score: int = 10000

    # CPC scoring
    cpc_optimal_range: Tuple[float, float] = (0.5, 3.0)
    cpc_max_score: float = 5.0

    # Threshold bands
    excellent_threshold: int = 60
    good_threshold: int = 40
    moderate_threshold: int = 20

    # Competition curvature (gamma > 1 emphasises low competition)
    competition_gamma_easy: float = 1.8
    competition_gamma_medium: float = 1.4
    competition_gamma_hard: float = 1.2

    # Competition caps by mode (for quick-win gating)
    easy_max_competition: float = 0.5
    medium_max_competition: float = 0.7
    hard_max_competition: float = 1.0

    # Quick-win thresholds by mode
    easy_quick_win_threshold: float = 45.0
    medium_quick_win_threshold: float = 55.0
    hard_quick_win_threshold: float = 65.0


def get_difficulty_weights(mode: DifficultyMode) -> Dict[str, float]:
    if mode == "easy":
        return {"volume": 0.25, "competition": 0.45, "cpc": 0.10, "longtail": 0.15, "commercial": 0.05}
    if mode == "hard":
        return {"volume": 0.45, "competition": 0.20, "cpc": 0.25, "longtail": 0.05, "commercial": 0.05}
    # medium
    return {"volume": 0.35, "competition": 0.30, "cpc": 0.20, "longtail": 0.10, "commercial": 0.05}


def _competition_gamma(mode: DifficultyMode, params: MultiFactorParams) -> float:
    return {
        "easy": params.competition_gamma_easy,
        "medium": params.competition_gamma_medium,
        "hard": params.competition_gamma_hard,
    }.get(mode, params.competition_gamma_medium)


def score_volume(volume: float, params: MultiFactorParams) -> float:
    if volume <= 0:
        return 0.0
    log_volume = math.log(max(1, volume), params.volume_log_base)
    log_max = math.log(params.volume_max_score, params.volume_log_base)
    return min(100.0, (log_volume / log_max) * 100.0)


def score_competition(competition: float, mode: DifficultyMode, params: MultiFactorParams) -> float:
    c = min(1.0, max(0.0, competition or 0.0))
    gamma = _competition_gamma(mode, params)
    return (1.0 - pow(c, gamma)) * 100.0


def score_cpc(cpc: float, params: MultiFactorParams) -> float:
    if cpc is None or cpc <= 0:
        return 0.0
    lo, hi = params.cpc_optimal_range
    if lo <= cpc <= hi:
        return 100.0
    if cpc < lo:
        return (cpc / lo) * 100.0
    excess = cpc - hi
    decay = math.exp(-excess / params.cpc_max_score)
    return 100.0 * decay


def score_longtail(keyword: str) -> float:
    words = len((keyword or "").strip().split())
    if words >= 5:
        return 100.0
    if words == 4:
        return 80.0
    if words == 3:
        return 60.0
    if words == 2:
        return 30.0
    return 0.0


def score_commercial_intent(keyword: str) -> float:
    # Lightweight heuristic to avoid importing heavier classifiers here
    k = (keyword or "").lower()
    transactional = ["buy", "price", "cost", "deal", "discount", "under "]
    commercial = ["best", "top", "review", "vs", "comparison", "alternative"]
    if any(w in k for w in transactional):
        return 100.0
    if any(w in k for w in commercial):
        return 80.0
    if any(w in k for w in ["login", "official", "website", "download"]):
        return 40.0
    return 20.0


def multifactor_score(
    keyword: str,
    volume: float,
    competition: float,
    cpc: Optional[float] = None,
    difficulty_mode: DifficultyMode = "medium",
    params: MultiFactorParams = MultiFactorParams(),
) -> Dict[str, Union[float, bool, str, Dict[str, float]]]:
    weights = get_difficulty_weights(difficulty_mode)

    v_score = score_volume(float(volume or 0.0), params)
    comp_score = score_competition(float(competition or 0.0), difficulty_mode, params)
    cpc_score = score_cpc(float(cpc or 0.0), params)
    lt_score = score_longtail(keyword)
    comm_score = score_commercial_intent(keyword)

    final = (
        weights["volume"] * v_score
        + weights["competition"] * comp_score
        + weights["cpc"] * cpc_score
        + weights["longtail"] * lt_score
        + weights["commercial"] * comm_score
    )

    # Gating
    max_comp = {
        "easy": params.easy_max_competition,
        "medium": params.medium_max_competition,
        "hard": params.hard_max_competition,
    }.get(difficulty_mode, params.medium_max_competition)
    quick_win_threshold = {
        "easy": params.easy_quick_win_threshold,
        "medium": params.medium_quick_win_threshold,
        "hard": params.hard_quick_win_threshold,
    }.get(difficulty_mode, params.medium_quick_win_threshold)

    words = len((keyword or "").split())
    is_quick = (
        float(competition or 0.0) <= max_comp
        and final >= quick_win_threshold
        and float(volume or 0.0) >= 50
        and words >= 3  # require 3+ words for quick-win flag
    )

    level = (
        "Excellent"
        if final >= params.excellent_threshold
        else "Good"
        if final >= params.good_threshold
        else "Moderate"
        if final >= params.moderate_threshold
        else "Difficult"
    )

    return {
        "score": round(final, 1),
        "opportunity_level": level,
        "is_quick_win": is_quick,
        "components": {
            "volume_score": round(v_score, 1),
            "competition_score": round(comp_score, 1),
            "cpc_score": round(cpc_score, 1),
            "longtail_score": round(lt_score, 1),
            "commercial_score": round(comm_score, 1),
        },
    }

