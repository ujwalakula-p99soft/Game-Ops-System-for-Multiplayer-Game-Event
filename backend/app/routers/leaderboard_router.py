from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_leaderboard_service
from app.schemas.leaderboard_schema import LeaderboardResponse
from app.services.leaderboard_service import LeaderboardService
from app.utils.enums import GameMode, Region

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])


@router.get("/global", response_model=LeaderboardResponse)
def get_global_leaderboard(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: LeaderboardService = Depends(get_leaderboard_service)
):
    return service.get_global_leaderboard(page=page, page_size=page_size)


@router.get("/region/{region}", response_model=LeaderboardResponse)
def get_region_leaderboard(
    region: Region,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: LeaderboardService = Depends(get_leaderboard_service)
):
    return service.get_region_leaderboard(region=region, page=page, page_size=page_size)


@router.get("/region/{region}/mode/{game_mode}", response_model=LeaderboardResponse)
def get_region_mode_leaderboard(
    region: Region,
    game_mode: GameMode,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: LeaderboardService = Depends(get_leaderboard_service)
):
    return service.get_region_mode_leaderboard(
        region=region, game_mode=game_mode, page=page, page_size=page_size
    )


@router.get("/mode/{game_mode}", response_model=LeaderboardResponse)
def get_mode_leaderboard(
    game_mode: GameMode,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: LeaderboardService = Depends(get_leaderboard_service)
):
    return service.get_mode_leaderboard(game_mode=game_mode, page=page, page_size=page_size)
