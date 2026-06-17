import math
from dataclasses import dataclass


@dataclass(frozen=True)
class PlayerMatchMetrics:
    kill_efficiency: float
    score_efficiency: float
    kd_ratio: float


@dataclass(frozen=True)
class AggregatedMetrics:
    avg_kill_efficiency: float
    avg_score_efficiency: float
    avg_kd_ratio: float


def compute_match_metrics(
    kills: int,
    score: int,
    deaths: int,
    match_duration_seconds: int
) -> PlayerMatchMetrics:
    duration = max(match_duration_seconds, 1)
    return PlayerMatchMetrics(
        kill_efficiency=kills / duration,
        score_efficiency=score / duration,
        kd_ratio=kills / max(deaths, 1)
    )


def aggregate_metrics(
    metrics: list[PlayerMatchMetrics]
) -> AggregatedMetrics:
    count = len(metrics)
    return AggregatedMetrics(
        avg_kill_efficiency=sum(m.kill_efficiency for m in metrics) / count,
        avg_score_efficiency=sum(m.score_efficiency for m in metrics) / count,
        avg_kd_ratio=sum(m.kd_ratio for m in metrics) / count
    )


def compute_mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def compute_std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = compute_mean(values)
    variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(variance)


def compute_z_score(value: float, mean: float, std: float) -> float:
    if std == 0.0:
        return 0.0
    return (value - mean) / std


def compute_anomaly_score(
    player_aggregated: AggregatedMetrics,
    pool_aggregated: list[AggregatedMetrics]
) -> float:
    if not pool_aggregated:
        return 0.0

    kill_eff_pool = [m.avg_kill_efficiency for m in pool_aggregated]
    score_eff_pool = [m.avg_score_efficiency for m in pool_aggregated]
    kd_pool = [m.avg_kd_ratio for m in pool_aggregated]

    z_kill = compute_z_score(
        player_aggregated.avg_kill_efficiency,
        compute_mean(kill_eff_pool),
        compute_std(kill_eff_pool)
    )
    z_score = compute_z_score(
        player_aggregated.avg_score_efficiency,
        compute_mean(score_eff_pool),
        compute_std(score_eff_pool)
    )
    z_kd = compute_z_score(
        player_aggregated.avg_kd_ratio,
        compute_mean(kd_pool),
        compute_std(kd_pool)
    )

    return (abs(z_kill) + abs(z_score) + abs(z_kd)) / 3.0
