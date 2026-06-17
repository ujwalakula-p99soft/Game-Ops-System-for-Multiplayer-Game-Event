from datetime import datetime

from pydantic import BaseModel


class SuspiciousPlayerResponse(BaseModel):
    player_id: str
    anomaly_score: float
    avg_kill_efficiency: float
    avg_score_efficiency: float
    avg_kd_ratio: float
    matches_evaluated: int
    flagged_at: datetime

    model_config = {"from_attributes": True}


class SuspiciousPlayersResponse(BaseModel):
    total: int
    entries: list[SuspiciousPlayerResponse]
