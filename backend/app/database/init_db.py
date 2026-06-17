from app.database.base import Base
from app.database.session import engine

from app.models.player_model import Player, PlayerModeStats
from app.models.match_model import Match, MatchResult
from app.models.suspicious_player_model import SuspiciousPlayer
from app.models.matchmaking_model import MatchmakingQueue


def init_db():
    Base.metadata.create_all(bind=engine)
