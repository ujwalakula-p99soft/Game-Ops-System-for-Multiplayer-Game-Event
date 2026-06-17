from dataclasses import dataclass

from app.utils.enums import GameMode, RankTier


LOBBY_SIZE: dict[GameMode, int] = {
    GameMode.SOLO: 1,
    GameMode.DUO: 2,
    GameMode.SQUAD: 4,
}


@dataclass(frozen=True)
class RelaxationWindow:
    ping_tolerance: int
    sr_tolerance: float | None


RELAXATION_WINDOWS: list[tuple[float, RelaxationWindow]] = [
    (5.0, RelaxationWindow(ping_tolerance=20, sr_tolerance=100.0)),
    (15.0, RelaxationWindow(ping_tolerance=50, sr_tolerance=300.0)),
    (float("inf"), RelaxationWindow(ping_tolerance=100, sr_tolerance=None)),
]


def compute_skill_rating(
    avg_score: float,
    avg_kills: float,
    avg_deaths: float
) -> float:
    return avg_score + (avg_kills * 10.0) - (avg_deaths * 5.0)


def resolve_rank(skill_rating: float) -> RankTier:
    if skill_rating < 500.0:
        return RankTier.BRONZE
    if skill_rating < 1500.0:
        return RankTier.SILVER
    if skill_rating < 3000.0:
        return RankTier.GOLD
    return RankTier.PLATINUM


def get_relaxation_window(wait_seconds: float) -> RelaxationWindow:
    for threshold, window in RELAXATION_WINDOWS:
        if wait_seconds <= threshold:
            return window
    return RELAXATION_WINDOWS[-1][1]


def is_compatible(
    candidate_ping: int,
    candidate_sr: float,
    target_ping: int,
    target_sr: float,
    window: RelaxationWindow
) -> bool:
    if abs(candidate_ping - target_ping) > window.ping_tolerance:
        return False
    if window.sr_tolerance is not None:
        if abs(candidate_sr - target_sr) > window.sr_tolerance:
            return False
    return True
