from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.utils.enums import GameMode


class MatchResultItem(BaseModel):
    player_id: str
    ping: int = Field(ge=0)
    score: int = Field(ge=0)
    kills: int = Field(ge=0)
    deaths: int = Field(ge=0)


class CreateMatchRequest(BaseModel):
    match_id: str
    game_mode: GameMode
    match_duration_seconds: int = Field(gt=0)
    results: list[MatchResultItem] = Field(min_length=1, max_length=100)

    @field_validator('results')
    @classmethod
    def validate_unique_players(cls, v):
        player_ids = [item.player_id for item in v]
        if len(player_ids) != len(set(player_ids)):
            raise ValueError("Each player may appear only once in match results")
        return v


class MatchResultResponse(BaseModel):
    player_id: str
    ping: int
    score: int
    kills: int
    deaths: int

    model_config = {"from_attributes": True}


class MatchResponse(BaseModel):
    match_id: str
    game_mode: GameMode
    match_duration_seconds: int
    created_at: datetime
    results: list[MatchResultResponse]

    model_config = {"from_attributes": True}
