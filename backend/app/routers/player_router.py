from fastapi import APIRouter, Depends

from app.core.dependencies import get_player_service
from app.schemas.player_schema import CreatePlayerRequest, PlayerResponse
from app.services.player_service import PlayerService

router = APIRouter(prefix="/players", tags=["Players"])


@router.post("", response_model=PlayerResponse)
def create_player(
    request: CreatePlayerRequest,
    service: PlayerService = Depends(get_player_service)
):
    return service.create_player(request)


@router.get("", response_model=list[PlayerResponse])
def get_all_players(
    service: PlayerService = Depends(get_player_service)
):
    return service.get_all_players()


@router.get("/{player_id}", response_model=PlayerResponse)
def get_player(
    player_id: str,
    service: PlayerService = Depends(get_player_service)
):
    return service.get_player(player_id)
