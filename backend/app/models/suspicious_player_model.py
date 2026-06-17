from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class SuspiciousPlayer(Base):
    __tablename__ = "suspicious_players"

    player_id: Mapped[str] = mapped_column(
        ForeignKey("players.player_id"), primary_key=True
    )
    anomaly_score: Mapped[float] = mapped_column(Float, nullable=False)
    avg_kill_efficiency: Mapped[float] = mapped_column(Float, nullable=False)
    avg_score_efficiency: Mapped[float] = mapped_column(Float, nullable=False)
    avg_kd_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    matches_evaluated: Mapped[int] = mapped_column(nullable=False)
    flagged_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None)
    )

    __table_args__ = (
        Index("idx_suspicious_players_anomaly_score", "anomaly_score"),
    )
