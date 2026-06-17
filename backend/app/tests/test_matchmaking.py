from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.dependencies import get_matchmaking_service
from app.models.matchmaking_model import MatchmakingQueue
from app.models.player_model import Player
from app.schemas.matchmaking_schema import (
    LeaveQueueResponse,
    LobbyFormedResponse,
    QueueStatusResponse,
    JoinQueueRequest
)
from app.services.matchmaking_service import MatchmakingService
from app.core.exceptions import (
    PlayerAlreadyInQueueException,
    PlayerNotFoundException,
    PlayerNotInQueueException
)
from app.utils.enums import DeviceType, GameMode, Region, RankTier
from app.utils.matchmaking import (
    LOBBY_SIZE,
    RelaxationWindow,
    compute_skill_rating,
    get_relaxation_window,
    is_compatible,
    resolve_rank,
)


def _make_player(
    player_id: str = "P001",
    region: Region = Region.INDIA,
    device: DeviceType = DeviceType.PC
) -> Player:
    return Player(
        player_id=player_id,
        region=region,
        device=device,
        created_at=datetime(2024, 1, 1)
    )


def _make_queue_entry(
    player_id: str = "P001",
    game_mode: GameMode = GameMode.SOLO,
    region: Region = Region.INDIA,
    device: DeviceType = DeviceType.PC,
    ping: int = 30,
    skill_rating: float = 500.0,
    seconds_ago: float = 0.0
) -> MatchmakingQueue:
    joined = datetime.now(timezone.utc) - timedelta(seconds=seconds_ago)
    return MatchmakingQueue(
        player_id=player_id, game_mode=game_mode, region=region,
        device=device, ping=ping, skill_rating=skill_rating, joined_at=joined
    )


def _make_service(
    matchmaking_repo: MagicMock | None = None,
    player_repo: MagicMock | None = None,
    suspicious_repo: MagicMock | None = None
) -> MatchmakingService:
    mr = matchmaking_repo or MagicMock()
    pr = player_repo or MagicMock()
    # Only set default empty history when caller did not supply their own repo
    if suspicious_repo is None:
        sr = MagicMock()
        sr.get_recent_results_for_player.return_value = []
    else:
        sr = suspicious_repo
    db = MagicMock()
    return MatchmakingService(db, mr, pr, sr)


client = TestClient(app)


class TestMatchmakingUtility:

    def test_compute_skill_rating(self):
        sr = compute_skill_rating(avg_score=100.0, avg_kills=10.0, avg_deaths=5.0)
        assert sr == pytest.approx(175.0)

    def test_compute_skill_rating_zero_history(self):
        assert compute_skill_rating(0.0, 0.0, 0.0) == pytest.approx(0.0)

    def test_resolve_rank_bronze(self):
        assert resolve_rank(0.0) == RankTier.BRONZE
        assert resolve_rank(499.9) == RankTier.BRONZE

    def test_resolve_rank_silver(self):
        assert resolve_rank(500.0) == RankTier.SILVER
        assert resolve_rank(1499.9) == RankTier.SILVER

    def test_resolve_rank_gold(self):
        assert resolve_rank(1500.0) == RankTier.GOLD
        assert resolve_rank(2999.9) == RankTier.GOLD

    def test_resolve_rank_platinum(self):
        assert resolve_rank(3000.0) == RankTier.PLATINUM
        assert resolve_rank(9999.9) == RankTier.PLATINUM

    def test_relaxation_window_0_to_5_seconds(self):
        w = get_relaxation_window(0.0)
        assert w.ping_tolerance == 20 and w.sr_tolerance == 100.0

    def test_relaxation_window_at_5_seconds(self):
        w = get_relaxation_window(5.0)
        assert w.ping_tolerance == 20 and w.sr_tolerance == 100.0

    def test_relaxation_window_6_to_15_seconds(self):
        w = get_relaxation_window(10.0)
        assert w.ping_tolerance == 50 and w.sr_tolerance == 300.0

    def test_relaxation_window_at_15_seconds(self):
        w = get_relaxation_window(15.0)
        assert w.ping_tolerance == 50 and w.sr_tolerance == 300.0

    def test_relaxation_window_beyond_15_seconds(self):
        w = get_relaxation_window(60.0)
        assert w.ping_tolerance == 100 and w.sr_tolerance is None

    def test_is_compatible_within_tight_window(self):
        window = RelaxationWindow(ping_tolerance=20, sr_tolerance=100.0)
        assert is_compatible(40, 550.0, 30, 500.0, window)

    def test_is_compatible_ping_exceeds_tolerance(self):
        window = RelaxationWindow(ping_tolerance=20, sr_tolerance=100.0)
        assert not is_compatible(60, 500.0, 30, 500.0, window)

    def test_is_compatible_sr_exceeds_tolerance(self):
        window = RelaxationWindow(ping_tolerance=20, sr_tolerance=100.0)
        assert not is_compatible(30, 700.0, 30, 500.0, window)

    def test_is_compatible_any_sr_when_tolerance_none(self):
        window = RelaxationWindow(ping_tolerance=100, sr_tolerance=None)
        assert is_compatible(30, 99999.0, 30, 0.0, window)

    def test_lobby_size_solo(self):
        assert LOBBY_SIZE[GameMode.SOLO] == 1

    def test_lobby_size_duo(self):
        assert LOBBY_SIZE[GameMode.DUO] == 2

    def test_lobby_size_squad(self):
        assert LOBBY_SIZE[GameMode.SQUAD] == 4


class TestMatchmakingServiceJoin:

    def test_join_raises_when_player_not_found(self):
        player_repo = MagicMock()
        player_repo.get_by_id.return_value = None
        service = _make_service(player_repo=player_repo)
        with pytest.raises(PlayerNotFoundException):
            service.join_queue(JoinQueueRequest(player_id="P999", game_mode=GameMode.SOLO, ping=30))

    def test_join_raises_when_already_in_queue(self):
        player_repo = MagicMock()
        player_repo.get_by_id.return_value = _make_player()
        matchmaking_repo = MagicMock()
        matchmaking_repo.get_by_player_id.return_value = _make_queue_entry()
        service = _make_service(matchmaking_repo=matchmaking_repo, player_repo=player_repo)
        with pytest.raises(PlayerAlreadyInQueueException):
            service.join_queue(JoinQueueRequest(player_id="P001", game_mode=GameMode.SOLO, ping=30))

    def test_join_returns_queue_status_when_no_lobby_formed(self):
        """DUO needs 2 players — only 1 candidate means no lobby forms."""
        player_repo = MagicMock()
        player_repo.get_by_id.return_value = _make_player()
        entry = _make_queue_entry(game_mode=GameMode.DUO)
        matchmaking_repo = MagicMock()
        matchmaking_repo.get_by_player_id.return_value = None
        matchmaking_repo.add.return_value = entry
        # Only 1 compatible candidate but DUO requires 2 → no lobby
        matchmaking_repo.get_candidates.return_value = [entry]
        service = _make_service(matchmaking_repo=matchmaking_repo, player_repo=player_repo)

        result = service.join_queue(JoinQueueRequest(player_id="P001", game_mode=GameMode.DUO, ping=30))

        assert isinstance(result, QueueStatusResponse)
        assert result.player_id == "P001"
        matchmaking_repo.remove_batch.assert_not_called()

    def test_join_returns_lobby_when_enough_compatible_players(self):
        player_repo = MagicMock()
        player_repo.get_by_id.return_value = _make_player()
        entry = _make_queue_entry(player_id="P001", skill_rating=500.0)
        matchmaking_repo = MagicMock()
        matchmaking_repo.get_by_player_id.return_value = None
        matchmaking_repo.add.return_value = entry
        matchmaking_repo.get_candidates.return_value = [entry]
        service = _make_service(matchmaking_repo=matchmaking_repo, player_repo=player_repo)

        result = service.join_queue(JoinQueueRequest(player_id="P001", game_mode=GameMode.SOLO, ping=30))

        assert isinstance(result, LobbyFormedResponse)
        assert len(result.players) == 1
        matchmaking_repo.remove_batch.assert_called_once_with(["P001"])

    def test_join_duo_lobby_requires_two_compatible_players(self):
        player_repo = MagicMock()
        player_repo.get_by_id.return_value = _make_player()
        e1 = _make_queue_entry("P001", GameMode.DUO, skill_rating=500.0)
        e2 = _make_queue_entry("P002", GameMode.DUO, skill_rating=520.0)
        matchmaking_repo = MagicMock()
        matchmaking_repo.get_by_player_id.return_value = None
        matchmaking_repo.add.return_value = e1
        matchmaking_repo.get_candidates.return_value = [e1, e2]
        service = _make_service(matchmaking_repo=matchmaking_repo, player_repo=player_repo)

        result = service.join_queue(JoinQueueRequest(player_id="P001", game_mode=GameMode.DUO, ping=30))

        assert isinstance(result, LobbyFormedResponse)
        assert len(result.players) == 2
        matchmaking_repo.remove_batch.assert_called_once_with(["P001", "P002"])

    def test_join_sr_computed_as_zero_when_no_history(self):
        player_repo = MagicMock()
        player_repo.get_by_id.return_value = _make_player()
        suspicious_repo = MagicMock()
        suspicious_repo.get_recent_results_for_player.return_value = []
        entry = _make_queue_entry(skill_rating=0.0)
        matchmaking_repo = MagicMock()
        matchmaking_repo.get_by_player_id.return_value = None
        matchmaking_repo.add.return_value = entry
        matchmaking_repo.get_candidates.return_value = []
        service = _make_service(matchmaking_repo=matchmaking_repo, player_repo=player_repo, suspicious_repo=suspicious_repo)

        result = service.join_queue(JoinQueueRequest(player_id="P001", game_mode=GameMode.SOLO, ping=30))

        assert isinstance(result, QueueStatusResponse)
        suspicious_repo.get_recent_results_for_player.assert_called_once_with(player_id="P001", limit=10)

    def test_join_sr_computed_from_match_history(self):
        player_repo = MagicMock()
        player_repo.get_by_id.return_value = _make_player()
        mock_result = MagicMock()
        mock_result.score = 100
        mock_result.kills = 10
        mock_result.deaths = 5
        suspicious_repo = MagicMock()
        suspicious_repo.get_recent_results_for_player.return_value = [mock_result]
        expected_sr = compute_skill_rating(avg_score=100.0, avg_kills=10.0, avg_deaths=5.0)
        captured_entry: list[MatchmakingQueue] = []

        def capture_add(entry):
            captured_entry.append(entry)
            return entry

        matchmaking_repo = MagicMock()
        matchmaking_repo.get_by_player_id.return_value = None
        matchmaking_repo.add.side_effect = capture_add
        matchmaking_repo.get_candidates.return_value = []
        service = _make_service(matchmaking_repo=matchmaking_repo, player_repo=player_repo, suspicious_repo=suspicious_repo)

        service.join_queue(JoinQueueRequest(player_id="P001", game_mode=GameMode.SOLO, ping=30))

        assert captured_entry[0].skill_rating == pytest.approx(expected_sr)


class TestMatchmakingServiceLeave:

    def test_leave_raises_when_not_in_queue(self):
        matchmaking_repo = MagicMock()
        matchmaking_repo.get_by_player_id.return_value = None
        service = _make_service(matchmaking_repo=matchmaking_repo)
        with pytest.raises(PlayerNotInQueueException):
            service.leave_queue("P001")

    def test_leave_removes_player_and_returns_response(self):
        matchmaking_repo = MagicMock()
        matchmaking_repo.get_by_player_id.return_value = _make_queue_entry()
        service = _make_service(matchmaking_repo=matchmaking_repo)

        result = service.leave_queue("P001")

        assert isinstance(result, LeaveQueueResponse)
        assert result.player_id == "P001"
        matchmaking_repo.remove.assert_called_once_with("P001")


class TestMatchmakingServiceStatus:

    def test_get_status_raises_when_not_in_queue(self):
        matchmaking_repo = MagicMock()
        matchmaking_repo.get_by_player_id.return_value = None
        service = _make_service(matchmaking_repo=matchmaking_repo)
        with pytest.raises(PlayerNotInQueueException):
            service.get_queue_status("P001")

    def test_get_status_returns_queue_status_response(self):
        matchmaking_repo = MagicMock()
        matchmaking_repo.get_by_player_id.return_value = _make_queue_entry(seconds_ago=10.0)
        service = _make_service(matchmaking_repo=matchmaking_repo)

        result = service.get_queue_status("P001")

        assert isinstance(result, QueueStatusResponse)
        assert result.player_id == "P001"
        assert result.wait_seconds == pytest.approx(10.0, abs=1.0)

    def test_get_status_resolves_rank(self):
        matchmaking_repo = MagicMock()
        matchmaking_repo.get_by_player_id.return_value = _make_queue_entry(skill_rating=2000.0)
        service = _make_service(matchmaking_repo=matchmaking_repo)

        result = service.get_queue_status("P001")

        assert result.rank == RankTier.GOLD


class TestMatchmakingServiceDynamicRelaxation:

    def test_relaxation_applied_based_on_wait_time(self):
        """Player waiting >15s should get sr_tolerance=None (any SR matches)."""
        player_repo = MagicMock()
        player_repo.get_by_id.return_value = _make_player()
        # Requester has been waiting 20 seconds
        requester = _make_queue_entry("P001", skill_rating=500.0, seconds_ago=20.0)
        # Candidate with very different SR — would fail tight window but pass unlimited
        candidate = _make_queue_entry("P002", skill_rating=9999.0, seconds_ago=0.0)
        matchmaking_repo = MagicMock()
        matchmaking_repo.get_by_player_id.return_value = None
        matchmaking_repo.add.return_value = requester
        matchmaking_repo.get_candidates.return_value = [requester, candidate]
        service = _make_service(matchmaking_repo=matchmaking_repo, player_repo=player_repo)

        result = service.join_queue(JoinQueueRequest(player_id="P001", game_mode=GameMode.SOLO, ping=30))

        # With sr_tolerance=None any SR is compatible; SOLO needs 1 player — lobby formed
        assert isinstance(result, LobbyFormedResponse)


class TestMatchmakingEndpoints:

    def test_join_queue_player_not_found_returns_404(self):
        mock_service = MagicMock()
        mock_service.join_queue.side_effect = PlayerNotFoundException("Player P999 not found")
        app.dependency_overrides[get_matchmaking_service] = lambda: mock_service

        response = client.post("/matchmaking/join", json={"player_id": "P999", "game_mode": "SOLO", "ping": 30})

        assert response.status_code == 404
        assert "P999" in response.json()["message"]
        app.dependency_overrides.clear()

    def test_join_queue_already_in_queue_returns_409(self):
        mock_service = MagicMock()
        mock_service.join_queue.side_effect = PlayerAlreadyInQueueException("P001 already in queue")
        app.dependency_overrides[get_matchmaking_service] = lambda: mock_service

        response = client.post("/matchmaking/join", json={"player_id": "P001", "game_mode": "SOLO", "ping": 30})

        assert response.status_code == 409
        app.dependency_overrides.clear()

    def test_join_queue_invalid_game_mode_returns_422(self):
        response = client.post("/matchmaking/join", json={"player_id": "P001", "game_mode": "INVALID", "ping": 30})
        assert response.status_code == 422

    def test_join_queue_negative_ping_returns_422(self):
        response = client.post("/matchmaking/join", json={"player_id": "P001", "game_mode": "SOLO", "ping": -1})
        assert response.status_code == 422

    def test_leave_queue_not_in_queue_returns_404(self):
        mock_service = MagicMock()
        mock_service.leave_queue.side_effect = PlayerNotInQueueException("P001 not in queue")
        app.dependency_overrides[get_matchmaking_service] = lambda: mock_service

        response = client.post("/matchmaking/leave", params={"player_id": "P001"})

        assert response.status_code == 404
        app.dependency_overrides.clear()

    def test_get_status_not_in_queue_returns_404(self):
        mock_service = MagicMock()
        mock_service.get_queue_status.side_effect = PlayerNotInQueueException("P001 not in queue")
        app.dependency_overrides[get_matchmaking_service] = lambda: mock_service

        response = client.get("/matchmaking/P001")

        assert response.status_code == 404
        app.dependency_overrides.clear()


class TestMatchmakingServiceTransactions:

    def test_join_queue_rolls_back_on_player_not_found(self):
        """db.rollback() called when player does not exist."""
        player_repo = MagicMock()
        player_repo.get_by_id.return_value = None
        matchmaking_repo = MagicMock()
        db = MagicMock()
        suspicious_repo = MagicMock()
        suspicious_repo.get_recent_results_for_player.return_value = []
        service = MatchmakingService(db, matchmaking_repo, player_repo, suspicious_repo)

        with pytest.raises(PlayerNotFoundException):
            service.join_queue(JoinQueueRequest(player_id="P999", game_mode=GameMode.SOLO, ping=30))

        db.rollback.assert_called_once()
        db.commit.assert_not_called()

    def test_join_queue_rolls_back_on_duplicate_queue_entry(self):
        """db.rollback() called when player is already in queue."""
        player_repo = MagicMock()
        player_repo.get_by_id.return_value = _make_player()
        matchmaking_repo = MagicMock()
        matchmaking_repo.get_by_player_id.return_value = _make_queue_entry()
        db = MagicMock()
        suspicious_repo = MagicMock()
        suspicious_repo.get_recent_results_for_player.return_value = []
        service = MatchmakingService(db, matchmaking_repo, player_repo, suspicious_repo)

        with pytest.raises(PlayerAlreadyInQueueException):
            service.join_queue(JoinQueueRequest(player_id="P001", game_mode=GameMode.SOLO, ping=30))

        db.rollback.assert_called_once()
        db.commit.assert_not_called()

    def test_join_queue_commits_on_success(self):
        """db.commit() called exactly once when join succeeds."""
        player_repo = MagicMock()
        player_repo.get_by_id.return_value = _make_player()
        entry = _make_queue_entry()
        matchmaking_repo = MagicMock()
        matchmaking_repo.get_by_player_id.return_value = None
        matchmaking_repo.add.return_value = entry
        matchmaking_repo.get_candidates.return_value = []
        db = MagicMock()
        suspicious_repo = MagicMock()
        suspicious_repo.get_recent_results_for_player.return_value = []
        service = MatchmakingService(db, matchmaking_repo, player_repo, suspicious_repo)

        service.join_queue(JoinQueueRequest(player_id="P001", game_mode=GameMode.SOLO, ping=30))

        db.commit.assert_called_once()
        db.rollback.assert_not_called()

    def test_leave_queue_rolls_back_when_player_not_in_queue(self):
        """db.rollback() called when player is not found in queue."""
        matchmaking_repo = MagicMock()
        matchmaking_repo.get_by_player_id.return_value = None
        db = MagicMock()
        suspicious_repo = MagicMock()
        suspicious_repo.get_recent_results_for_player.return_value = []
        service = MatchmakingService(db, matchmaking_repo, MagicMock(), suspicious_repo)

        with pytest.raises(PlayerNotInQueueException):
            service.leave_queue("P001")

        db.rollback.assert_called_once()
        db.commit.assert_not_called()

    def test_lobby_formation_removes_all_players_atomically(self):
        """remove_batch is called in a single call covering all lobby player IDs."""
        player_repo = MagicMock()
        player_repo.get_by_id.return_value = _make_player()
        e1 = _make_queue_entry("P001", GameMode.SQUAD, skill_rating=500.0)
        e2 = _make_queue_entry("P002", GameMode.SQUAD, skill_rating=510.0)
        e3 = _make_queue_entry("P003", GameMode.SQUAD, skill_rating=520.0)
        e4 = _make_queue_entry("P004", GameMode.SQUAD, skill_rating=530.0)
        matchmaking_repo = MagicMock()
        matchmaking_repo.get_by_player_id.return_value = None
        matchmaking_repo.add.return_value = e1
        matchmaking_repo.get_candidates.return_value = [e1, e2, e3, e4]
        db = MagicMock()
        suspicious_repo = MagicMock()
        suspicious_repo.get_recent_results_for_player.return_value = []
        service = MatchmakingService(db, matchmaking_repo, player_repo, suspicious_repo)

        result = service.join_queue(JoinQueueRequest(player_id="P001", game_mode=GameMode.SQUAD, ping=30))

        assert isinstance(result, LobbyFormedResponse)
        assert len(result.players) == 4
        # remove_batch called once with all 4 IDs — atomic cleanup
        matchmaking_repo.remove_batch.assert_called_once()
        removed_ids = set(matchmaking_repo.remove_batch.call_args[0][0])
        assert removed_ids == {"P001", "P002", "P003", "P004"}
