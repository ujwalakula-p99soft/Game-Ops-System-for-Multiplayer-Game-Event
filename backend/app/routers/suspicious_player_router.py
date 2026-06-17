from fastapi import APIRouter, Depends

from app.core.dependencies import get_suspicious_player_service
from app.schemas.suspicious_player_schema import SuspiciousPlayersResponse
from app.services.suspicious_player_service import SuspiciousPlayerService

router = APIRouter(prefix="/suspicious-players", tags=["Suspicious Players"])


@router.get("", response_model=SuspiciousPlayersResponse)
def get_suspicious_players(
    service: SuspiciousPlayerService = Depends(get_suspicious_player_service)
):
    return service.get_suspicious_players()
