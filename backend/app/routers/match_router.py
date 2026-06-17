from fastapi import APIRouter, Depends

from app.core.dependencies import get_match_service
from app.schemas.match_schema import CreateMatchRequest, MatchResponse
from app.services.match_service import MatchService

router = APIRouter(prefix="/matches", tags=["Matches"])


@router.post("", response_model=MatchResponse)
def create_match(
    request: CreateMatchRequest,
    service: MatchService = Depends(get_match_service)
):
    return service.create_match(request)
