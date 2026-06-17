from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.player_model import Player


class PlayerRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, player: Player) -> Player:
        self.db.add(player)
        return player

    def get_by_id(self, player_id: str) -> Player | None:
        stmt = select(Player).where(Player.player_id == player_id)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def get_all(self) -> list[Player]:
        stmt = select(Player)
        result = self.db.execute(stmt)
        return result.scalars().all()
