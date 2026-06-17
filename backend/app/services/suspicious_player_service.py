from datetime import UTC, datetime

from app.models.suspicious_player_model import SuspiciousPlayer
from app.schemas.suspicious_player_schema import SuspiciousPlayerResponse, SuspiciousPlayersResponse
from app.repositories.suspicious_player_repository import SuspiciousPlayerRepository
from app.repositories.player_repository import PlayerRepository
from app.utils.stats import (
    AggregatedMetrics,
    aggregate_metrics,
    compute_anomaly_score,
    compute_match_metrics
)
from app.core.logger import logger


class SuspiciousPlayerService:
    RECENT_MATCH_LIMIT: int = 10
    MIN_MATCHES_REQUIRED: int = 3
    ANOMALY_THRESHOLD_SIGMA: float = 2.0

    def __init__(
        self,
        suspicious_player_repository: SuspiciousPlayerRepository,
        player_repository: PlayerRepository
    ):
        self.suspicious_player_repository = suspicious_player_repository
        self.player_repository = player_repository

    def _build_player_aggregated(self, player_id: str) -> tuple[AggregatedMetrics, int] | None:
        results = self.suspicious_player_repository.get_recent_results_for_player(
            player_id=player_id, limit=self.RECENT_MATCH_LIMIT
        )
        if len(results) < self.MIN_MATCHES_REQUIRED:
            return None
        metrics = [
            compute_match_metrics(
                kills=r.kills,
                score=r.score,
                deaths=r.deaths,
                match_duration_seconds=self.suspicious_player_repository.get_match_duration(r.match_id)
            )
            for r in results
        ]
        return aggregate_metrics(metrics), len(results)

    def _build_pool_aggregated(self, player_id: str) -> list[AggregatedMetrics]:
        player = self.player_repository.get_by_id(player_id)
        if not player:
            return []
        pool_players = self.suspicious_player_repository.get_players_in_pool(
            region=player.region, device=player.device
        )
        pool_player_ids = [p.player_id for p in pool_players if p.player_id != player_id]
        if not pool_player_ids:
            return []
        all_results = self.suspicious_player_repository.get_pool_player_results_batch(
            pool_player_ids, self.RECENT_MATCH_LIMIT
        )
        pool_aggregated = []
        for pid in pool_player_ids:
            results = all_results.get(pid, [])
            if len(results) >= self.MIN_MATCHES_REQUIRED:
                metrics = [
                    compute_match_metrics(
                        kills=r.kills,
                        score=r.score,
                        deaths=r.deaths,
                        match_duration_seconds=self.suspicious_player_repository.get_match_duration(r.match_id)
                    )
                    for r in results
                ]
                pool_aggregated.append(aggregate_metrics(metrics))
        return pool_aggregated

    def evaluate_player(self, player_id: str) -> None:
        player_result = self._build_player_aggregated(player_id)
        if player_result is None:
            logger.info(f"Player {player_id} skipped: insufficient matches")
            return
        player_aggregated, match_count = player_result
        pool_aggregated = self._build_pool_aggregated(player_id)
        anomaly_score = compute_anomaly_score(
            player_aggregated=player_aggregated,
            pool_aggregated=pool_aggregated
        )
        if anomaly_score >= self.ANOMALY_THRESHOLD_SIGMA:
            suspicious = SuspiciousPlayer(
                player_id=player_id,
                anomaly_score=anomaly_score,
                avg_kill_efficiency=player_aggregated.avg_kill_efficiency,
                avg_score_efficiency=player_aggregated.avg_score_efficiency,
                avg_kd_ratio=player_aggregated.avg_kd_ratio,
                matches_evaluated=match_count,
                flagged_at=datetime.now(UTC).replace(tzinfo=None)
            )
            self.suspicious_player_repository.upsert_suspicious_player(suspicious)
            logger.info(f"Player {player_id} flagged: anomaly_score={anomaly_score:.4f}, matches={match_count}")
        else:
            self.suspicious_player_repository.remove_suspicious_player(player_id)
            logger.info(f"Player {player_id} cleared: anomaly_score={anomaly_score:.4f}")

    def get_suspicious_players(self) -> SuspiciousPlayersResponse:
        entries = self.suspicious_player_repository.get_all()
        logger.info(f"Suspicious players fetched: count={len(entries)}")
        return SuspiciousPlayersResponse(
            total=len(entries),
            entries=[SuspiciousPlayerResponse.model_validate(entry) for entry in entries]
        )
