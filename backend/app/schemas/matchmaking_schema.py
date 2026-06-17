from datetime import datetime

from pydantic import BaseModel, Field

from app.utils.enums import DeviceType, GameMode, Region, RankTier


class JoinQueueRequest(BaseModel):
    player_id: str
    game_mode: GameMode
    ping: int = Field(ge=0)


class QueueStatusResponse(BaseModel):
    player_id: str
    game_mode: GameMode
    region: Region
    device: DeviceType
    ping: int
    skill_rating: float
    rank: RankTier
    joined_at: datetime
    wait_seconds: float

    model_config = {"from_attributes": True}


class LobbyPlayerResponse(BaseModel):
    player_id: str
    skill_rating: float
    rank: RankTier
    ping: int

    model_config = {"from_attributes": True}


class LobbyFormedResponse(BaseModel):
    game_mode: GameMode
    region: Region
    players: list[LobbyPlayerResponse]


class LeaveQueueResponse(BaseModel):
    player_id: str
    message: str
