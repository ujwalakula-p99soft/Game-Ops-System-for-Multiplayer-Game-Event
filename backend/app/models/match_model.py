from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.utils.enums import GameMode


class Match(Base):
    __tablename__ = "matches"

    match_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    game_mode: Mapped[GameMode] = mapped_column(Enum(GameMode), nullable=False)
    match_duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None)
    )

    results: Mapped[list["MatchResult"]] = relationship(
        "MatchResult",
        back_populates="match",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_matches_game_mode", "game_mode"),
        Index("idx_matches_created_at", "created_at"),
    )


class MatchResult(Base):
    __tablename__ = "match_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[str] = mapped_column(ForeignKey("matches.match_id"), nullable=False)
    player_id: Mapped[str] = mapped_column(ForeignKey("players.player_id"), nullable=False)
    ping: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    kills: Mapped[int] = mapped_column(Integer, nullable=False)
    deaths: Mapped[int] = mapped_column(Integer, nullable=False)

    match: Mapped["Match"] = relationship("Match", back_populates="results")

    __table_args__ = (
        Index("idx_match_results_match_id", "match_id"),
        Index("idx_match_results_player_id", "player_id"),
        Index("idx_match_results_player_id_match_id", "player_id", "match_id"),
    )
