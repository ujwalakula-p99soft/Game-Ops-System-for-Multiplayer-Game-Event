from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.matchmaking_model import MatchmakingQueue
from app.utils.enums import DeviceType, GameMode, Region


class MatchmakingRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_player_id(self, player_id: str) -> MatchmakingQueue | None:
        stmt = select(MatchmakingQueue).where(MatchmakingQueue.player_id == player_id)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: MatchmakingQueue) -> MatchmakingQueue:
        self.db.add(entry)
        return entry

    def remove(self, player_id: str) -> None:
        stmt = delete(MatchmakingQueue).where(MatchmakingQueue.player_id == player_id)
        self.db.execute(stmt)

    def get_candidates(
        self, game_mode: GameMode, region: Region, device: DeviceType, lock: bool = False
    ) -> list[MatchmakingQueue]:
        stmt = (
            select(MatchmakingQueue)
            .where(
                MatchmakingQueue.game_mode == game_mode,
                MatchmakingQueue.region == region,
                MatchmakingQueue.device == device
            )
            .order_by(MatchmakingQueue.joined_at.asc())
        )
        if lock:
            stmt = stmt.with_for_update()
        result = self.db.execute(stmt)
        return result.scalars().all()

    def remove_batch(self, player_ids: list[str]) -> None:
        stmt = delete(MatchmakingQueue).where(MatchmakingQueue.player_id.in_(player_ids))
        self.db.execute(stmt)
