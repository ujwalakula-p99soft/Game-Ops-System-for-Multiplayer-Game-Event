from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.utils.enums import DeviceType, GameMode, Region


class MatchmakingQueue(Base):
    __tablename__ = "matchmaking_queue"

    player_id: Mapped[str] = mapped_column(
        ForeignKey("players.player_id"), primary_key=True
    )
    game_mode: Mapped[GameMode] = mapped_column(Enum(GameMode), nullable=False)
    region: Mapped[Region] = mapped_column(Enum(Region), nullable=False)
    device: Mapped[DeviceType] = mapped_column(Enum(DeviceType), nullable=False)
    ping: Mapped[int] = mapped_column(Integer, nullable=False)
    skill_rating: Mapped[float] = mapped_column(Float, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), nullable=False
    )

    __table_args__ = (
        Index("idx_matchmaking_queue_region_device_game_mode", "region", "device", "game_mode"),
        Index("idx_matchmaking_queue_skill_rating", "skill_rating"),
        Index("idx_matchmaking_queue_joined_at", "joined_at"),
    )
