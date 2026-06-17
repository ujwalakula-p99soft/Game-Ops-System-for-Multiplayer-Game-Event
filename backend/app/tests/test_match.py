from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.dependencies import get_match_service
from app.models.match_model import Match, MatchResult
from app.schemas.match_schema import CreateMatchRequest
from app.core.exceptions import MatchAlreadyExistsException, PlayerNotFoundException
from app.utils.enums import GameMode


def _make_match(
    match_id: str = "M001",
    game_mode: GameMode = GameMode.SOLO,
    duration: int = 300,
    results: list[MatchResult] | None = None
) -> Match:
    match = Match(
        match_id=match_id,
        game_mode=game_mode,
        match_duration_seconds=duration,
        created_at=datetime(2024, 1, 1, 0, 0, 0)
    )
    match.results = results or []
    return match


def _make_result(player_id: str = "P001", match_id: str = "M001") -> MatchResult:
    return MatchResult(
        id=1, match_id=match_id, player_id=player_id,
        ping=30, score=100, kills=5, deaths=2
    )


client = TestClient(app)

VALID_PAYLOAD = {
    "match_id": "M001",
    "game_mode": "SOLO",
    "match_duration_seconds": 300,
    "results": [{"player_id": "P001", "ping": 30, "score": 100, "kills": 5, "deaths": 2}]
}


class TestCreateMatchEndpoint:

    def test_create_match_success(self):
        match = _make_match(results=[_make_result()])
        mock_service = MagicMock()
        mock_service.create_match.return_value = match
        app.dependency_overrides[get_match_service] = lambda: mock_service

        response = client.post("/matches", json=VALID_PAYLOAD)

        assert response.status_code == 200
        data = response.json()
        assert data["match_id"] == "M001"
        assert data["game_mode"] == "SOLO"
        assert data["match_duration_seconds"] == 300
        assert len(data["results"]) == 1
        assert data["results"][0]["player_id"] == "P001"
        app.dependency_overrides.clear()

    def test_create_match_player_not_found_returns_404(self):
        mock_service = MagicMock()
        mock_service.create_match.side_effect = PlayerNotFoundException("Player P999 not found")
        app.dependency_overrides[get_match_service] = lambda: mock_service

        payload = {**VALID_PAYLOAD, "results": [
            {"player_id": "P999", "ping": 30, "score": 100, "kills": 5, "deaths": 2}
        ]}
        response = client.post("/matches", json=payload)

        assert response.status_code == 404
        assert "P999" in response.json()["message"]
        app.dependency_overrides.clear()

    def test_create_match_duplicate_id_returns_409(self):
        mock_service = MagicMock()
        mock_service.create_match.side_effect = MatchAlreadyExistsException("Match M001 already exists")
        app.dependency_overrides[get_match_service] = lambda: mock_service

        response = client.post("/matches", json=VALID_PAYLOAD)

        assert response.status_code == 409
        assert "M001" in response.json()["message"]
        app.dependency_overrides.clear()

    def test_create_match_invalid_game_mode_returns_422(self):
        response = client.post("/matches", json={**VALID_PAYLOAD, "game_mode": "INVALID"})
        assert response.status_code == 422

    def test_create_match_zero_duration_returns_422(self):
        response = client.post("/matches", json={**VALID_PAYLOAD, "match_duration_seconds": 0})
        assert response.status_code == 422

    def test_create_match_empty_results_returns_422(self):
        response = client.post("/matches", json={**VALID_PAYLOAD, "results": []})
        assert response.status_code == 422

    def test_create_match_exceeds_max_players_returns_422(self):
        results = [
            {"player_id": f"P{i:03}", "ping": 30, "score": 100, "kills": 5, "deaths": 2}
            for i in range(101)
        ]
        response = client.post("/matches", json={**VALID_PAYLOAD, "results": results})
        assert response.status_code == 422

    def test_create_match_negative_kills_returns_422(self):
        payload = {**VALID_PAYLOAD, "results": [
            {"player_id": "P001", "ping": 30, "score": 100, "kills": -1, "deaths": 2}
        ]}
        response = client.post("/matches", json=payload)
        assert response.status_code == 422


class TestMatchService:

    def test_create_match_rejects_duplicate_match_id(self):
        from app.services.match_service import MatchService

        mock_db = MagicMock()
        mock_match_repo = MagicMock()
        mock_match_repo.get_by_id.return_value = _make_match()
        mock_player_repo = MagicMock()
        mock_leaderboard_repo = MagicMock()
        mock_suspicious_repo = MagicMock()

        service = MatchService(
            mock_db, mock_match_repo, mock_player_repo,
            mock_leaderboard_repo, mock_suspicious_repo
        )
        request = CreateMatchRequest(
            match_id="M001", game_mode=GameMode.SOLO, match_duration_seconds=300,
            results=[{"player_id": "P001", "ping": 30, "score": 100, "kills": 5, "deaths": 2}]
        )

        with pytest.raises(MatchAlreadyExistsException) as exc_info:
            service.create_match(request)

        assert "M001" in str(exc_info.value)
        mock_match_repo.create.assert_not_called()
        mock_player_repo.get_by_id.assert_not_called()

    def test_create_match_validates_all_players(self):
        from app.services.match_service import MatchService

        mock_db = MagicMock()
        mock_match_repo = MagicMock()
        mock_match_repo.get_by_id.return_value = None
        mock_player_repo = MagicMock()
        mock_player_repo.get_by_id.return_value = None
        mock_leaderboard_repo = MagicMock()
        mock_suspicious_repo = MagicMock()
        mock_suspicious_repo.get_recent_results_for_player.return_value = []

        service = MatchService(
            mock_db, mock_match_repo, mock_player_repo,
            mock_leaderboard_repo, mock_suspicious_repo
        )
        request = CreateMatchRequest(
            match_id="M001", game_mode=GameMode.SOLO, match_duration_seconds=300,
            results=[{"player_id": "P999", "ping": 30, "score": 100, "kills": 5, "deaths": 2}]
        )

        with pytest.raises(PlayerNotFoundException) as exc_info:
            service.create_match(request)

        assert "P999" in str(exc_info.value)
        mock_match_repo.create.assert_not_called()

    def test_create_match_persists_when_players_valid(self):
        from app.services.match_service import MatchService

        mock_db = MagicMock()
        mock_match_repo = MagicMock()
        mock_match_repo.get_by_id.return_value = None
        mock_player_repo = MagicMock()
        mock_player_repo.get_by_id.return_value = MagicMock()
        mock_leaderboard_repo = MagicMock()
        mock_suspicious_repo = MagicMock()
        mock_suspicious_repo.get_recent_results_for_player.return_value = []

        match = _make_match(results=[_make_result()])
        mock_match_repo.create.return_value = match

        service = MatchService(
            mock_db, mock_match_repo, mock_player_repo,
            mock_leaderboard_repo, mock_suspicious_repo
        )
        request = CreateMatchRequest(
            match_id="M001", game_mode=GameMode.SOLO, match_duration_seconds=300,
            results=[{"player_id": "P001", "ping": 30, "score": 100, "kills": 5, "deaths": 2}]
        )

        result_match = service.create_match(request)

        mock_match_repo.create.assert_called_once()
        assert result_match.match_id == "M001"

    def test_create_match_validates_each_player_in_results(self):
        from app.services.match_service import MatchService

        mock_db = MagicMock()
        mock_match_repo = MagicMock()
        mock_match_repo.get_by_id.return_value = None
        mock_player_repo = MagicMock()
        mock_leaderboard_repo = MagicMock()
        mock_suspicious_repo = MagicMock()
        mock_suspicious_repo.get_recent_results_for_player.return_value = []

        existing_player = MagicMock()
        mock_player_repo.get_by_id.side_effect = (
            lambda pid: existing_player if pid == "P001" else None
        )

        service = MatchService(
            mock_db, mock_match_repo, mock_player_repo,
            mock_leaderboard_repo, mock_suspicious_repo
        )
        request = CreateMatchRequest(
            match_id="M002", game_mode=GameMode.DUO, match_duration_seconds=200,
            results=[
                {"player_id": "P001", "ping": 20, "score": 50, "kills": 2, "deaths": 1},
                {"player_id": "P999", "ping": 20, "score": 50, "kills": 2, "deaths": 1},
            ]
        )

        with pytest.raises(PlayerNotFoundException) as exc_info:
            service.create_match(request)

        assert "P999" in str(exc_info.value)


class TestMatchServiceTransactions:

    def test_create_match_rolls_back_on_player_not_found(self):
        """db.rollback() must be called when a player is missing."""
        from app.services.match_service import MatchService

        mock_db = MagicMock()
        mock_match_repo = MagicMock()
        mock_match_repo.get_by_id.return_value = None
        mock_player_repo = MagicMock()
        mock_player_repo.get_by_id.return_value = None  # trigger failure
        mock_leaderboard_repo = MagicMock()
        mock_suspicious_repo = MagicMock()

        service = MatchService(
            mock_db, mock_match_repo, mock_player_repo,
            mock_leaderboard_repo, mock_suspicious_repo
        )
        request = CreateMatchRequest(
            match_id="M001", game_mode=GameMode.SOLO, match_duration_seconds=300,
            results=[{"player_id": "P999", "ping": 30, "score": 100, "kills": 5, "deaths": 2}]
        )

        with pytest.raises(PlayerNotFoundException):
            service.create_match(request)

        mock_db.rollback.assert_called_once()
        mock_db.commit.assert_not_called()

    def test_create_match_rolls_back_on_leaderboard_repo_failure(self):
        """db.rollback() is called when any repo raises mid-transaction."""
        from app.services.match_service import MatchService

        mock_db = MagicMock()
        mock_match_repo = MagicMock()
        mock_match_repo.get_by_id.return_value = None
        mock_player_repo = MagicMock()
        mock_player_repo.get_by_id.return_value = MagicMock()
        mock_leaderboard_repo = MagicMock()
        mock_leaderboard_repo.add_ranking_score.side_effect = RuntimeError("DB write failed")
        mock_suspicious_repo = MagicMock()
        mock_suspicious_repo.get_recent_results_for_player.return_value = []

        saved_match = _make_match(results=[_make_result()])
        mock_match_repo.create.return_value = saved_match

        service = MatchService(
            mock_db, mock_match_repo, mock_player_repo,
            mock_leaderboard_repo, mock_suspicious_repo
        )
        request = CreateMatchRequest(
            match_id="M001", game_mode=GameMode.SOLO, match_duration_seconds=300,
            results=[{"player_id": "P001", "ping": 30, "score": 100, "kills": 5, "deaths": 2}]
        )

        with pytest.raises(RuntimeError, match="DB write failed"):
            service.create_match(request)

        mock_db.rollback.assert_called_once()
        mock_db.commit.assert_not_called()

    def test_create_match_commits_on_success(self):
        """db.commit() is called exactly once on a fully successful match creation."""
        from app.services.match_service import MatchService

        mock_db = MagicMock()
        mock_match_repo = MagicMock()
        mock_match_repo.get_by_id.return_value = None
        mock_player_repo = MagicMock()
        mock_player_repo.get_by_id.return_value = MagicMock()
        mock_leaderboard_repo = MagicMock()
        mock_suspicious_repo = MagicMock()
        mock_suspicious_repo.get_recent_results_for_player.return_value = []

        saved_match = _make_match(results=[_make_result()])
        mock_match_repo.create.return_value = saved_match

        service = MatchService(
            mock_db, mock_match_repo, mock_player_repo,
            mock_leaderboard_repo, mock_suspicious_repo
        )
        request = CreateMatchRequest(
            match_id="M001", game_mode=GameMode.SOLO, match_duration_seconds=300,
            results=[{"player_id": "P001", "ping": 30, "score": 100, "kills": 5, "deaths": 2}]
        )

        service.create_match(request)

        mock_db.commit.assert_called_once()
        mock_db.rollback.assert_not_called()
