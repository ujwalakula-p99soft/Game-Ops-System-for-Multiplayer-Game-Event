from datetime import UTC, datetime

from app.core.exceptions import PlayerNotFoundException
from app.models.player_model import Player
from app.repositories.player_repository import PlayerRepository
from app.schemas.player_schema import CreatePlayerRequest
from app.core.logger import logger


class PlayerService:
    def __init__(self, repository: PlayerRepository):
        self.repository = repository

    def create_player(self, request: CreatePlayerRequest) -> Player:
        player = Player(
            player_id=request.player_id,
            region=request.region,
            device=request.device,
            # Naive UTC for TIMESTAMP WITHOUT TIME ZONE columns.
            created_at=datetime.now(UTC).replace(tzinfo=None),
        )
        self.repository.create(player)
        self.repository.db.commit()
        self.repository.db.refresh(player)
        logger.info(f"Player created: {request.player_id}")
        return player

    def get_all_players(self) -> list[Player]:
        players = self.repository.get_all()
        logger.info(f"All players fetched: count={len(players)}")
        return players

    def get_player(self, player_id: str) -> Player:
        player = self.repository.get_by_id(player_id)
        if not player:
            raise PlayerNotFoundException(f"Player {player_id} not found")
        return player

    def get_all_players(self) -> list[Player]:
        players = self.repository.get_all()
        logger.info(f"All players fetched: count={len(players)}")
        return players
