from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.repositories.player_repository import PlayerRepository
from app.repositories.match_repository import MatchRepository
from app.repositories.leaderboard_repository import LeaderboardRepository
from app.repositories.suspicious_player_repository import SuspiciousPlayerRepository
from app.repositories.matchmaking_repository import MatchmakingRepository
from app.services.player_service import PlayerService
from app.services.match_service import MatchService
from app.services.leaderboard_service import LeaderboardService
from app.services.suspicious_player_service import SuspiciousPlayerService
from app.services.matchmaking_service import MatchmakingService


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_player_repository(db: Session = Depends(get_db)) -> PlayerRepository:
    return PlayerRepository(db)


def get_player_service(
    repository: PlayerRepository = Depends(get_player_repository)
) -> PlayerService:
    return PlayerService(repository)


def get_match_repository(db: Session = Depends(get_db)) -> MatchRepository:
    return MatchRepository(db)


def get_leaderboard_repository(db: Session = Depends(get_db)) -> LeaderboardRepository:
    return LeaderboardRepository(db)


def get_suspicious_player_repository(
    db: Session = Depends(get_db)
) -> SuspiciousPlayerRepository:
    return SuspiciousPlayerRepository(db)


def get_matchmaking_repository(db: Session = Depends(get_db)) -> MatchmakingRepository:
    return MatchmakingRepository(db)


def get_leaderboard_service(
    leaderboard_repository: LeaderboardRepository = Depends(get_leaderboard_repository)
) -> LeaderboardService:
    return LeaderboardService(leaderboard_repository)


def get_suspicious_player_service(
    suspicious_player_repository: SuspiciousPlayerRepository = Depends(get_suspicious_player_repository),
    player_repository: PlayerRepository = Depends(get_player_repository)
) -> SuspiciousPlayerService:
    return SuspiciousPlayerService(suspicious_player_repository, player_repository)


def get_match_service(
    db: Session = Depends(get_db),
    match_repository: MatchRepository = Depends(get_match_repository),
    player_repository: PlayerRepository = Depends(get_player_repository),
    leaderboard_repository: LeaderboardRepository = Depends(get_leaderboard_repository),
    suspicious_player_repository: SuspiciousPlayerRepository = Depends(get_suspicious_player_repository)
) -> MatchService:
    return MatchService(db, match_repository, player_repository, leaderboard_repository, suspicious_player_repository)


def get_matchmaking_service(
    db: Session = Depends(get_db),
    matchmaking_repository: MatchmakingRepository = Depends(get_matchmaking_repository),
    player_repository: PlayerRepository = Depends(get_player_repository),
    suspicious_player_repository: SuspiciousPlayerRepository = Depends(get_suspicious_player_repository)
) -> MatchmakingService:
    return MatchmakingService(db, matchmaking_repository, player_repository, suspicious_player_repository)
