from unittest.mock import MagicMock
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.dependencies import get_player_service
from app.models.player_model import Player
from app.schemas.player_schema import PlayerResponse
from app.services.player_service import PlayerService
from app.core.exceptions import PlayerNotFoundException
from app.utils.enums import DeviceType, Region


def _make_player(
    player_id: str = "P001",
    region: Region = Region.INDIA,
    device: DeviceType = DeviceType.ANDROID
) -> Player:
    return Player(
        player_id=player_id,
        region=region,
        device=device,
        created_at=datetime(2024, 1, 1, 0, 0, 0)
    )


client = TestClient(app)


class TestCreatePlayerEndpoint:

    def test_create_player_returns_200(self):
        mock_service = MagicMock()
        mock_service.create_player.return_value = _make_player()
        app.dependency_overrides[get_player_service] = lambda: mock_service

        response = client.post("/players", json={
            "player_id": "P001", "region": "India", "device": "Android"
        })

        assert response.status_code == 200
        assert response.json()["player_id"] == "P001"
        app.dependency_overrides.clear()

    def test_create_player_invalid_region_returns_422(self):
        response = client.post("/players", json={
            "player_id": "P001", "region": "INVALID", "device": "Android"
        })
        assert response.status_code == 422

    def test_create_player_invalid_device_returns_422(self):
        response = client.post("/players", json={
            "player_id": "P001", "region": "India", "device": "INVALID"
        })
        assert response.status_code == 422

    def test_create_player_missing_field_returns_422(self):
        response = client.post("/players", json={"player_id": "P001", "region": "India"})
        assert response.status_code == 422


class TestGetPlayerEndpoint:

    def test_get_player_returns_200(self):
        mock_service = MagicMock()
        mock_service.get_player.return_value = _make_player()
        app.dependency_overrides[get_player_service] = lambda: mock_service

        response = client.get("/players/P001")

        assert response.status_code == 200
        assert response.json()["player_id"] == "P001"
        app.dependency_overrides.clear()

    def test_get_player_not_found_returns_404(self):
        mock_service = MagicMock()
        mock_service.get_player.side_effect = PlayerNotFoundException("Player P999 not found")
        app.dependency_overrides[get_player_service] = lambda: mock_service

        response = client.get("/players/P999")

        assert response.status_code == 404
        assert "P999" in response.json()["message"]
        app.dependency_overrides.clear()


class TestGetAllPlayersEndpoint:

    def test_get_all_players_returns_200(self):
        mock_service = MagicMock()
        mock_service.get_all_players.return_value = [
            _make_player("P001"),
            _make_player("P002"),
        ]
        app.dependency_overrides[get_player_service] = lambda: mock_service

        response = client.get("/players")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["player_id"] == "P001"
        app.dependency_overrides.clear()


class TestPlayerService:

    def test_create_player_calls_repository(self):
        mock_repo = MagicMock()
        mock_repo.create.return_value = _make_player()
        service = PlayerService(mock_repo)

        from app.schemas.player_schema import CreatePlayerRequest
        request = CreatePlayerRequest(player_id="P001", region=Region.INDIA, device=DeviceType.ANDROID)
        result = service.create_player(request)

        mock_repo.create.assert_called_once()
        assert result.player_id == "P001"

    def test_get_player_raises_when_not_found(self):
        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = None
        service = PlayerService(mock_repo)

        with pytest.raises(PlayerNotFoundException) as exc_info:
            service.get_player("P999")

        assert "P999" in str(exc_info.value)

    def test_get_player_returns_player_when_found(self):
        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = _make_player()
        service = PlayerService(mock_repo)

        result = service.get_player("P001")

        assert result.player_id == "P001"

    def test_get_all_players_returns_repository_results(self):
        mock_repo = MagicMock()
        mock_repo.get_all.return_value = [_make_player("P001"), _make_player("P002")]
        service = PlayerService(mock_repo)

        result = service.get_all_players()

        mock_repo.get_all.assert_called_once()
        assert len(result) == 2
        assert result[0].player_id == "P001"
