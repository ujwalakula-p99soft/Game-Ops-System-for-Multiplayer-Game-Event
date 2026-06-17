from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.exceptions import MatchAlreadyExistsException, PlayerNotFoundException
from app.models.match_model import Match, MatchResult
from app.models.suspicious_player_model import SuspiciousPlayer
from app.repositories.match_repository import MatchRepository
from app.repositories.player_repository import PlayerRepository
from app.repositories.leaderboard_repository import LeaderboardRepository
from app.repositories.suspicious_player_repository import SuspiciousPlayerRepository
from app.schemas.match_schema import CreateMatchRequest
from app.utils.stats import aggregate_metrics, compute_anomaly_score, compute_match_metrics
from app.core.logger import logger


class MatchService:
    def __init__(
        self,
        db: Session,
        match_repository: MatchRepository,
        player_repository: PlayerRepository,
        leaderboard_repository: LeaderboardRepository,
        suspicious_player_repository: SuspiciousPlayerRepository
    ):
        self.db = db
        self.match_repository = match_repository
        self.player_repository = player_repository
        self.leaderboard_repository = leaderboard_repository
        self.suspicious_player_repository = suspicious_player_repository

    def create_match(self, request: CreateMatchRequest) -> Match:
        try:
            if self.match_repository.get_by_id(request.match_id):
                raise MatchAlreadyExistsException(f"Match {request.match_id} already exists")

            # Validate all players exist
            for result_item in request.results:
                player = self.player_repository.get_by_id(result_item.player_id)
                if not player:
                    raise PlayerNotFoundException(f"Player {result_item.player_id} not found")

            # Create match and results
            match = Match(
                match_id=request.match_id,
                game_mode=request.game_mode,
                match_duration_seconds=request.match_duration_seconds
            )
            results = [
                MatchResult(
                    match_id=request.match_id,
                    player_id=item.player_id,
                    ping=item.ping,
                    score=item.score,
                    kills=item.kills,
                    deaths=item.deaths
                )
                for item in request.results
            ]
            saved_match = self.match_repository.create(match, results)

            # Update leaderboard ranking scores (cumulative per mode)
            for item in request.results:
                score_to_add = (item.kills * 1000) + item.score - (item.deaths * 50)
                self.leaderboard_repository.add_ranking_score(
                    player_id=item.player_id,
                    game_mode=request.game_mode,
                    score_to_add=score_to_add,
                    kills=item.kills,
                    score=item.score,
                    deaths=item.deaths
                )

            # Suspicious player detection (population-relative, requires ≥3 matches)
            for item in request.results:
                player_id = item.player_id
                recent = self.suspicious_player_repository.get_recent_results_for_player(
                    player_id, limit=10
                )
                if len(recent) >= 3:
                    player_agg = aggregate_metrics([
                        compute_match_metrics(
                            kills=r.kills,
                            score=r.score,
                            deaths=r.deaths,
                            match_duration_seconds=self.suspicious_player_repository.get_match_duration(r.match_id)
                        )
                        for r in recent
                    ])
                    player = self.player_repository.get_by_id(player_id)
                    pool_players = self.suspicious_player_repository.get_players_in_pool(
                        region=player.region, device=player.device
                    )
                    pool_ids = [p.player_id for p in pool_players if p.player_id != player_id]
                    pool_results = self.suspicious_player_repository.get_pool_player_results_batch(pool_ids, 10)
                    pool_aggs = [
                        aggregate_metrics([
                            compute_match_metrics(
                                kills=r.kills,
                                score=r.score,
                                deaths=r.deaths,
                                match_duration_seconds=self.suspicious_player_repository.get_match_duration(r.match_id)
                            )
                            for r in pool_results.get(pid, [])
                        ])
                        for pid in pool_ids
                        if len(pool_results.get(pid, [])) >= 3
                    ]
                    anomaly_score = compute_anomaly_score(player_agg, pool_aggs)
                    if anomaly_score >= 2.0:
                        sp = SuspiciousPlayer(
                            player_id=player_id,
                            anomaly_score=anomaly_score,
                            avg_kill_efficiency=player_agg.avg_kill_efficiency,
                            avg_score_efficiency=player_agg.avg_score_efficiency,
                            avg_kd_ratio=player_agg.avg_kd_ratio,
                            matches_evaluated=len(recent),
                            flagged_at=datetime.now(UTC).replace(tzinfo=None)
                        )
                        self.suspicious_player_repository.upsert_suspicious_player(sp)
                        logger.info(f"Player {player_id} flagged: anomaly_score={anomaly_score:.4f}")
                    else:
                        self.suspicious_player_repository.remove_suspicious_player(player_id)
                        logger.info(f"Player {player_id} cleared: anomaly_score={anomaly_score:.4f}")

            self.db.commit()
            logger.info(
                f"Match created: {saved_match.match_id}, "
                f"mode: {saved_match.game_mode}, "
                f"players: {len(results)}"
            )
            return saved_match
        except Exception as e:
            self.db.rollback()
            raise e
