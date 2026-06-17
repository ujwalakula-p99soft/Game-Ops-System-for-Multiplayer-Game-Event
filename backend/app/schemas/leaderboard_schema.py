from pydantic import BaseModel

from app.utils.enums import Region


class LeaderboardEntryResponse(BaseModel):
    rank: int
    player_id: str
    ranking_score: int
    region: Region

    model_config = {"from_attributes": True}


class LeaderboardResponse(BaseModel):
    total: int
    page: int
    page_size: int
    entries: list[LeaderboardEntryResponse]
