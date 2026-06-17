from fastapi import APIRouter, Depends

from app.core.dependencies import get_matchmaking_service
from app.schemas.matchmaking_schema import (
    JoinQueueRequest,
    LeaveQueueResponse,
    LobbyFormedResponse,
    QueueStatusResponse
)
from app.services.matchmaking_service import MatchmakingService

router = APIRouter(prefix="/matchmaking", tags=["Matchmaking"])


@router.post("/join", response_model=QueueStatusResponse | LobbyFormedResponse)
def join_queue(
    request: JoinQueueRequest,
    service: MatchmakingService = Depends(get_matchmaking_service)
):
    return service.join_queue(request)


@router.post("/leave", response_model=LeaveQueueResponse)
def leave_queue(
    player_id: str,
    service: MatchmakingService = Depends(get_matchmaking_service)
):
    return service.leave_queue(player_id)


@router.get("/{player_id}", response_model=QueueStatusResponse)
def get_queue_status(
    player_id: str,
    service: MatchmakingService = Depends(get_matchmaking_service)
):
    return service.get_queue_status(player_id)
