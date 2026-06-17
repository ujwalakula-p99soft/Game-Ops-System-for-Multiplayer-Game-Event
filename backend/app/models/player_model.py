from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.utils.enums import DeviceType, GameMode, Region


class Player(Base):
    __tablename__ = "players"

    player_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    region: Mapped[Region] = mapped_column(Enum(Region), nullable=False)
    device: Mapped[DeviceType] = mapped_column(Enum(DeviceType), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None)
    )

    mode_stats: Mapped[list["PlayerModeStats"]] = relationship(
        "PlayerModeStats",
        back_populates="player",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_players_region", "region"),
        Index("idx_players_device", "device"),
        Index("idx_players_region_device", "region", "device"),
    )


class PlayerModeStats(Base):
    __tablename__ = "player_mode_stats"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    player_id: Mapped[str] = mapped_column(
        ForeignKey("players.player_id"), nullable=False
    )
    game_mode: Mapped[GameMode] = mapped_column(Enum(GameMode), nullable=False)
    ranking_score: Mapped[int] = mapped_column(default=0)
    total_kills: Mapped[int] = mapped_column(default=0)
    total_score: Mapped[int] = mapped_column(default=0)
    total_deaths: Mapped[int] = mapped_column(default=0)
    matches_played: Mapped[int] = mapped_column(default=0)

    player: Mapped["Player"] = relationship("Player", back_populates="mode_stats")

    __table_args__ = (
        Index("idx_player_mode_stats_player_id_game_mode", "player_id", "game_mode", unique=True),
        Index("idx_player_mode_stats_game_mode_ranking_score", "game_mode", "ranking_score"),
    )
