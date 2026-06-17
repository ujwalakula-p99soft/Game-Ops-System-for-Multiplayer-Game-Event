from datetime import UTC, datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import (
    PlayerAlreadyInQueueException,
    PlayerNotFoundException,
    PlayerNotInQueueException
)
from app.models.matchmaking_model import MatchmakingQueue
from app.schemas.matchmaking_schema import (
    JoinQueueRequest,
    LeaveQueueResponse,
    LobbyFormedResponse,
    LobbyPlayerResponse,
    QueueStatusResponse
)
from app.repositories.matchmaking_repository import MatchmakingRepository
from app.repositories.player_repository import PlayerRepository
from app.repositories.suspicious_player_repository import SuspiciousPlayerRepository
from app.utils.matchmaking import (
    LOBBY_SIZE,
    compute_skill_rating,
    get_relaxation_window,
    is_compatible,
    resolve_rank
)
from app.core.logger import logger


class MatchmakingService:
    def __init__(
        self,
        db: Session,
        matchmaking_repository: MatchmakingRepository,
        player_repository: PlayerRepository,
        suspicious_player_repository: SuspiciousPlayerRepository
    ):
        self.db = db
        self.matchmaking_repository = matchmaking_repository
        self.player_repository = player_repository
        self.suspicious_player_repository = suspicious_player_repository

    def _compute_player_sr(self, player_id: str) -> float:
        results = self.suspicious_player_repository.get_recent_results_for_player(
            player_id=player_id, limit=10
        )
        if not results:
            return 0.0
        count = len(results)
        return compute_skill_rating(
            avg_score=sum(r.score for r in results) / count,
            avg_kills=sum(r.kills for r in results) / count,
            avg_deaths=sum(r.deaths for r in results) / count
        )

    def _seconds_in_queue(self, entry: MatchmakingQueue) -> float:
        now = datetime.now(timezone.utc)
        joined = entry.joined_at
        if joined.tzinfo is None:
            joined = joined.replace(tzinfo=timezone.utc)
        return (now - joined).total_seconds()

    def join_queue(self, request: JoinQueueRequest) -> QueueStatusResponse | LobbyFormedResponse:
        try:
            player = self.player_repository.get_by_id(request.player_id)
            if not player:
                raise PlayerNotFoundException(f"Player {request.player_id} not found")

            existing = self.matchmaking_repository.get_by_player_id(request.player_id)
            if existing:
                raise PlayerAlreadyInQueueException(f"Player {request.player_id} already in queue")

            skill_rating = self._compute_player_sr(request.player_id)
            entry = MatchmakingQueue(
                player_id=request.player_id,
                game_mode=request.game_mode,
                region=player.region,
                device=player.device,
                ping=request.ping,
                skill_rating=skill_rating,
                joined_at=datetime.now(UTC).replace(tzinfo=None)
            )
            saved_entry = self.matchmaking_repository.add(entry)
            logger.info(
                f"Player {request.player_id} joined queue: "
                f"mode={request.game_mode}, region={player.region}, sr={skill_rating:.2f}"
            )

            lobby = self._attempt_match(saved_entry)
            self.db.commit()

            if lobby is not None:
                return lobby

            return QueueStatusResponse(
                player_id=saved_entry.player_id,
                game_mode=saved_entry.game_mode,
                region=saved_entry.region,
                device=saved_entry.device,
                ping=saved_entry.ping,
                skill_rating=saved_entry.skill_rating,
                rank=resolve_rank(saved_entry.skill_rating),
                joined_at=saved_entry.joined_at,
                wait_seconds=0.0
            )
        except Exception as e:
            self.db.rollback()
            raise e

    def _attempt_match(self, requester: MatchmakingQueue) -> LobbyFormedResponse | None:
        candidates = self.matchmaking_repository.get_candidates(
            game_mode=requester.game_mode,
            region=requester.region,
            device=requester.device,
            lock=True
        )
        required = LOBBY_SIZE[requester.game_mode]
        window = get_relaxation_window(self._seconds_in_queue(requester))
        compatible: list[MatchmakingQueue] = []
        for candidate in candidates:
            if not is_compatible(
                candidate_ping=candidate.ping,
                candidate_sr=candidate.skill_rating,
                target_ping=requester.ping,
                target_sr=requester.skill_rating,
                window=window
            ):
                continue
            compatible.append(candidate)
            if len(compatible) == required:
                break

        if len(compatible) < required:
            return None

        player_ids = [c.player_id for c in compatible]
        self.matchmaking_repository.remove_batch(player_ids)
        logger.info(f"Lobby formed: mode={requester.game_mode}, region={requester.region}, players={player_ids}")

        return LobbyFormedResponse(
            game_mode=requester.game_mode,
            region=requester.region,
            players=[
                LobbyPlayerResponse(
                    player_id=c.player_id,
                    skill_rating=c.skill_rating,
                    rank=resolve_rank(c.skill_rating),
                    ping=c.ping
                )
                for c in compatible
            ]
        )

    def leave_queue(self, player_id: str) -> LeaveQueueResponse:
        try:
            existing = self.matchmaking_repository.get_by_player_id(player_id)
            if not existing:
                raise PlayerNotInQueueException(f"Player {player_id} not in queue")
            self.matchmaking_repository.remove(player_id)
            self.db.commit()
            logger.info(f"Player {player_id} left queue")
            return LeaveQueueResponse(
                player_id=player_id,
                message=f"Player {player_id} removed from matchmaking queue"
            )
        except Exception as e:
            self.db.rollback()
            raise e

    def get_queue_status(self, player_id: str) -> QueueStatusResponse:
        entry = self.matchmaking_repository.get_by_player_id(player_id)
        if not entry:
            raise PlayerNotInQueueException(f"Player {player_id} not in queue")
        return QueueStatusResponse(
            player_id=entry.player_id,
            game_mode=entry.game_mode,
            region=entry.region,
            device=entry.device,
            ping=entry.ping,
            skill_rating=entry.skill_rating,
            rank=resolve_rank(entry.skill_rating),
            joined_at=entry.joined_at,
            wait_seconds=self._seconds_in_queue(entry)
        )
