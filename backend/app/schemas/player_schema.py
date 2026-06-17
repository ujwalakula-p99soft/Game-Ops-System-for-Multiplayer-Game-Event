from datetime import datetime

from pydantic import BaseModel

from app.utils.enums import DeviceType, Region


class CreatePlayerRequest(BaseModel):
    player_id: str
    region: Region
    device: DeviceType


class PlayerResponse(BaseModel):
    player_id: str
    region: Region
    device: DeviceType
    created_at: datetime

    model_config = {"from_attributes": True}
