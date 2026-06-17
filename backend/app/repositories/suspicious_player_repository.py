from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.match_model import Match, MatchResult
from app.models.player_model import Player
from app.models.suspicious_player_model import SuspiciousPlayer
from app.utils.enums import DeviceType, Region


class SuspiciousPlayerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_recent_results_for_player(self, player_id: str, limit: int) -> list[MatchResult]:
        stmt = (
            select(MatchResult)
            .join(Match, MatchResult.match_id == Match.match_id)
            .where(MatchResult.player_id == player_id)
            .order_by(Match.created_at.desc())
            .limit(limit)
        )
        return self.db.execute(stmt).scalars().all()

    def get_match_duration(self, match_id: str) -> int:
        stmt = select(Match.match_duration_seconds).where(Match.match_id == match_id)
        return self.db.execute(stmt).scalar_one_or_none() or 1

    def get_players_in_pool(self, region: Region, device: DeviceType) -> list[Player]:
        stmt = select(Player).where(Player.region == region, Player.device == device)
        return self.db.execute(stmt).scalars().all()

    def get_pool_player_results_batch(
        self, player_ids: list[str], limit: int
    ) -> dict[str, list[MatchResult]]:
        stmt = (
            select(MatchResult)
            .join(Match, MatchResult.match_id == Match.match_id)
            .where(MatchResult.player_id.in_(player_ids))
            .order_by(MatchResult.player_id, Match.created_at.desc())
        )
        all_results = self.db.execute(stmt).scalars().all()
        grouped: dict[str, list[MatchResult]] = {}
        for res in all_results:
            if res.player_id not in grouped:
                grouped[res.player_id] = []
            if len(grouped[res.player_id]) < limit:
                grouped[res.player_id].append(res)
        return grouped

    def upsert_suspicious_player(self, suspicious_player: SuspiciousPlayer) -> SuspiciousPlayer:
        existing = self.db.execute(
            select(SuspiciousPlayer).where(
                SuspiciousPlayer.player_id == suspicious_player.player_id
            )
        ).scalar_one_or_none()
        if existing:
            existing.anomaly_score = suspicious_player.anomaly_score
            existing.avg_kill_efficiency = suspicious_player.avg_kill_efficiency
            existing.avg_score_efficiency = suspicious_player.avg_score_efficiency
            existing.avg_kd_ratio = suspicious_player.avg_kd_ratio
            existing.matches_evaluated = suspicious_player.matches_evaluated
            existing.flagged_at = suspicious_player.flagged_at
            return existing
        self.db.add(suspicious_player)
        return suspicious_player

    def remove_suspicious_player(self, player_id: str) -> None:
        self.db.execute(
            delete(SuspiciousPlayer).where(SuspiciousPlayer.player_id == player_id)
        )

    def get_all(self) -> list[SuspiciousPlayer]:
        stmt = select(SuspiciousPlayer).order_by(SuspiciousPlayer.anomaly_score.desc())
        return self.db.execute(stmt).scalars().all()
