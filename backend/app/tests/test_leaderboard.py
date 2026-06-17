from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.dependencies import get_leaderboard_service
from app.models.player_model import Player, PlayerModeStats
from app.schemas.leaderboard_schema import LeaderboardEntryResponse, LeaderboardResponse
from app.services.leaderboard_service import LeaderboardService
from app.utils.enums import GameMode, Region


def _make_player(
    player_id: str = "P001",
    region: Region = Region.INDIA,
    ranking_score: int = 5000,
    game_mode: GameMode = GameMode.SOLO
) -> Player:
    player = Player(
        player_id=player_id,
        region=region,
        created_at=datetime(2024, 1, 1, 0, 0, 0)
    )
    stats = PlayerModeStats(
        player_id=player_id,
        game_mode=game_mode,
        ranking_score=ranking_score,
        total_kills=0, total_score=0, total_deaths=0, matches_played=0
    )
    player.mode_stats = [stats]
    return player


def _make_leaderboard_response(
    entries: list[LeaderboardEntryResponse] | None = None
) -> LeaderboardResponse:
    return LeaderboardResponse(
        total=1, page=1, page_size=20,
        entries=entries or [
            LeaderboardEntryResponse(rank=1, player_id="P001", ranking_score=5000, region=Region.INDIA)
        ]
    )


client = TestClient(app)


class TestGlobalLeaderboardEndpoint:

    def test_get_global_leaderboard_returns_200(self):
        mock_service = MagicMock()
        mock_service.get_global_leaderboard.return_value = _make_leaderboard_response()
        app.dependency_overrides[get_leaderboard_service] = lambda: mock_service

        response = client.get("/leaderboard/global")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["entries"][0]["rank"] == 1
        assert data["entries"][0]["player_id"] == "P001"
        app.dependency_overrides.clear()

    def test_get_global_leaderboard_default_pagination(self):
        mock_service = MagicMock()
        mock_service.get_global_leaderboard.return_value = _make_leaderboard_response()
        app.dependency_overrides[get_leaderboard_service] = lambda: mock_service

        client.get("/leaderboard/global")

        mock_service.get_global_leaderboard.assert_called_once_with(page=1, page_size=20)
        app.dependency_overrides.clear()

    def test_get_global_leaderboard_custom_pagination(self):
        mock_service = MagicMock()
        mock_service.get_global_leaderboard.return_value = _make_leaderboard_response()
        app.dependency_overrides[get_leaderboard_service] = lambda: mock_service

        client.get("/leaderboard/global?page=2&page_size=10")

        mock_service.get_global_leaderboard.assert_called_once_with(page=2, page_size=10)
        app.dependency_overrides.clear()

    def test_get_global_leaderboard_invalid_page_returns_422(self):
        assert client.get("/leaderboard/global?page=0").status_code == 422

    def test_get_global_leaderboard_page_size_exceeds_max_returns_422(self):
        assert client.get("/leaderboard/global?page_size=101").status_code == 422


class TestRegionLeaderboardEndpoint:

    def test_get_region_leaderboard_returns_200(self):
        mock_service = MagicMock()
        mock_service.get_region_leaderboard.return_value = _make_leaderboard_response()
        app.dependency_overrides[get_leaderboard_service] = lambda: mock_service

        assert client.get("/leaderboard/region/India").status_code == 200
        app.dependency_overrides.clear()

    def test_get_region_leaderboard_passes_region_to_service(self):
        mock_service = MagicMock()
        mock_service.get_region_leaderboard.return_value = _make_leaderboard_response()
        app.dependency_overrides[get_leaderboard_service] = lambda: mock_service

        client.get("/leaderboard/region/India")

        mock_service.get_region_leaderboard.assert_called_once_with(
            region=Region.INDIA, page=1, page_size=20
        )
        app.dependency_overrides.clear()

    def test_get_region_leaderboard_invalid_region_returns_422(self):
        assert client.get("/leaderboard/region/INVALID").status_code == 422


class TestModeLeaderboardEndpoint:

    def test_get_mode_leaderboard_solo_returns_200(self):
        mock_service = MagicMock()
        mock_service.get_mode_leaderboard.return_value = _make_leaderboard_response()
        app.dependency_overrides[get_leaderboard_service] = lambda: mock_service

        assert client.get("/leaderboard/mode/SOLO").status_code == 200
        app.dependency_overrides.clear()

    def test_get_mode_leaderboard_duo_returns_200(self):
        mock_service = MagicMock()
        mock_service.get_mode_leaderboard.return_value = _make_leaderboard_response()
        app.dependency_overrides[get_leaderboard_service] = lambda: mock_service

        assert client.get("/leaderboard/mode/DUO").status_code == 200
        app.dependency_overrides.clear()

    def test_get_mode_leaderboard_squad_returns_200(self):
        mock_service = MagicMock()
        mock_service.get_mode_leaderboard.return_value = _make_leaderboard_response()
        app.dependency_overrides[get_leaderboard_service] = lambda: mock_service

        assert client.get("/leaderboard/mode/SQUAD").status_code == 200
        app.dependency_overrides.clear()

    def test_get_mode_leaderboard_passes_game_mode_to_service(self):
        mock_service = MagicMock()
        mock_service.get_mode_leaderboard.return_value = _make_leaderboard_response()
        app.dependency_overrides[get_leaderboard_service] = lambda: mock_service

        client.get("/leaderboard/mode/DUO")

        mock_service.get_mode_leaderboard.assert_called_once_with(
            game_mode=GameMode.DUO, page=1, page_size=20
        )
        app.dependency_overrides.clear()

    def test_get_mode_leaderboard_invalid_mode_returns_422(self):
        assert client.get("/leaderboard/mode/INVALID").status_code == 422


class TestLeaderboardService:

    # ── Ranking formula ────────────────────────────────────────────────────

    def test_ranking_score_formula(self):
        """Ranking Score = (Kills × 1000) + Score - (Deaths × 50)"""
        service = LeaderboardService(MagicMock())
        assert service._compute_ranking_score(kills=10, score=500, deaths=3) == 10350

    def test_ranking_score_zero_deaths(self):
        service = LeaderboardService(MagicMock())
        assert service._compute_ranking_score(kills=5, score=200, deaths=0) == 5200

    def test_ranking_score_zero_kills(self):
        service = LeaderboardService(MagicMock())
        # 0 + 100 - 100 = 0
        assert service._compute_ranking_score(kills=0, score=100, deaths=2) == 0

    def test_ranking_score_kills_dominate_ordering(self):
        """Higher kills outrank high raw score."""
        service = LeaderboardService(MagicMock())
        assert service._compute_ranking_score(kills=10, score=0, deaths=0) > \
               service._compute_ranking_score(kills=0, score=9999, deaths=0)

    def test_ranking_score_deaths_penalize(self):
        service = LeaderboardService(MagicMock())
        assert service._compute_ranking_score(kills=5, score=200, deaths=0) > \
               service._compute_ranking_score(kills=5, score=200, deaths=3)

    # ── Tie-breakers ───────────────────────────────────────────────────────

    def test_tie_breaker_kills_over_score(self):
        """Two players with same ranking_score: higher kills wins."""
        service = LeaderboardService(MagicMock())
        # kills*1000 dominates — player with 10 kills ranks higher than 9 kills + more score
        more_kills = service._compute_ranking_score(kills=10, score=0, deaths=0)
        fewer_kills = service._compute_ranking_score(kills=9, score=999, deaths=0)
        assert more_kills > fewer_kills

    def test_tie_breaker_fewer_deaths(self):
        """Same kills and score: fewer deaths ranks higher."""
        service = LeaderboardService(MagicMock())
        assert service._compute_ranking_score(kills=5, score=300, deaths=1) > \
               service._compute_ranking_score(kills=5, score=300, deaths=5)

    # ── _build_entries ──────────────────────────────────────────────────────

    def test_build_entries_assigns_correct_rank(self):
        service = LeaderboardService(MagicMock())
        players = [
            _make_player("P001", Region.INDIA, 9000),
            _make_player("P002", Region.SEA, 7000),
            _make_player("P003", Region.EUROPE, 5000)
        ]
        entries = service._build_entries(players, offset=0)
        assert entries[0].rank == 1
        assert entries[1].rank == 2
        assert entries[2].rank == 3

    def test_build_entries_assigns_correct_rank_with_offset(self):
        """Page 3 page_size 10 → ranks start at 21."""
        service = LeaderboardService(MagicMock())
        players = [_make_player("P021", Region.INDIA, 3000), _make_player("P022", Region.SEA, 2000)]
        entries = service._build_entries(players, offset=20)
        assert entries[0].rank == 21
        assert entries[1].rank == 22

    def test_build_entries_sums_all_mode_stats_for_global(self):
        """Global ranking_score = sum across all mode_stats rows."""
        service = LeaderboardService(MagicMock())
        player = Player(player_id="P001", region=Region.INDIA, created_at=datetime(2024, 1, 1))
        player.mode_stats = [
            PlayerModeStats(player_id="P001", game_mode=GameMode.SOLO,
                            ranking_score=3000, total_kills=0, total_score=0, total_deaths=0, matches_played=0),
            PlayerModeStats(player_id="P001", game_mode=GameMode.DUO,
                            ranking_score=2000, total_kills=0, total_score=0, total_deaths=0, matches_played=0),
        ]
        entries = service._build_entries([player], offset=0)
        assert entries[0].ranking_score == 5000

    # ── Global leaderboard ──────────────────────────────────────────────────

    def test_get_global_leaderboard_calls_repository(self):
        mock_repo = MagicMock()
        mock_repo.get_global.return_value = (1, [_make_player()])
        service = LeaderboardService(mock_repo)

        result = service.get_global_leaderboard(page=1, page_size=20)

        mock_repo.get_global.assert_called_once_with(offset=0, limit=20)
        assert result.total == 1
        assert result.page == 1
        assert result.page_size == 20

    def test_get_global_leaderboard_page_2_offset(self):
        mock_repo = MagicMock()
        mock_repo.get_global.return_value = (50, [])
        LeaderboardService(mock_repo).get_global_leaderboard(page=3, page_size=10)
        mock_repo.get_global.assert_called_once_with(offset=20, limit=10)

    def test_get_global_leaderboard_pagination_metadata(self):
        mock_repo = MagicMock()
        mock_repo.get_global.return_value = (100, [_make_player()])
        result = LeaderboardService(mock_repo).get_global_leaderboard(page=2, page_size=10)
        assert result.total == 100
        assert result.page == 2
        assert result.page_size == 10

    # ── Region leaderboard ──────────────────────────────────────────────────

    def test_get_region_leaderboard_india(self):
        mock_repo = MagicMock()
        mock_repo.get_by_region.return_value = (2, [
            _make_player("P001", Region.INDIA, 9000),
            _make_player("P002", Region.INDIA, 7000)
        ])
        result = LeaderboardService(mock_repo).get_region_leaderboard(
            region=Region.INDIA, page=1, page_size=20
        )
        mock_repo.get_by_region.assert_called_once_with(region=Region.INDIA, offset=0, limit=20)
        assert result.total == 2
        assert len(result.entries) == 2

    def test_get_region_leaderboard_sea(self):
        mock_repo = MagicMock()
        mock_repo.get_by_region.return_value = (1, [_make_player("P001", Region.SEA)])
        LeaderboardService(mock_repo).get_region_leaderboard(region=Region.SEA, page=1, page_size=20)
        mock_repo.get_by_region.assert_called_once_with(region=Region.SEA, offset=0, limit=20)

    def test_get_region_leaderboard_europe(self):
        mock_repo = MagicMock()
        mock_repo.get_by_region.return_value = (1, [_make_player("P001", Region.EUROPE)])
        LeaderboardService(mock_repo).get_region_leaderboard(region=Region.EUROPE, page=1, page_size=20)
        mock_repo.get_by_region.assert_called_once_with(region=Region.EUROPE, offset=0, limit=20)

    # ── Mode leaderboard ────────────────────────────────────────────────────

    def test_get_mode_leaderboard_solo(self):
        mock_repo = MagicMock()
        mock_repo.get_by_game_mode.return_value = (1, [_make_player()])
        result = LeaderboardService(mock_repo).get_mode_leaderboard(
            game_mode=GameMode.SOLO, page=1, page_size=20
        )
        mock_repo.get_by_game_mode.assert_called_once_with(game_mode=GameMode.SOLO, offset=0, limit=20)
        assert result.total == 1

    def test_get_mode_leaderboard_duo(self):
        mock_repo = MagicMock()
        mock_repo.get_by_game_mode.return_value = (1, [_make_player(game_mode=GameMode.DUO)])
        LeaderboardService(mock_repo).get_mode_leaderboard(game_mode=GameMode.DUO, page=1, page_size=20)
        mock_repo.get_by_game_mode.assert_called_once_with(game_mode=GameMode.DUO, offset=0, limit=20)

    def test_get_mode_leaderboard_squad(self):
        mock_repo = MagicMock()
        mock_repo.get_by_game_mode.return_value = (1, [_make_player(game_mode=GameMode.SQUAD)])
        LeaderboardService(mock_repo).get_mode_leaderboard(game_mode=GameMode.SQUAD, page=1, page_size=20)
        mock_repo.get_by_game_mode.assert_called_once_with(game_mode=GameMode.SQUAD, offset=0, limit=20)

    def test_get_mode_leaderboard_returns_mode_specific_score(self):
        """Mode leaderboard shows only that mode's ranking_score, not the total."""
        mock_repo = MagicMock()
        player = Player(player_id="P001", region=Region.INDIA, created_at=datetime(2024, 1, 1))
        player.mode_stats = [
            PlayerModeStats(player_id="P001", game_mode=GameMode.SOLO,
                            ranking_score=8000, total_kills=0, total_score=0, total_deaths=0, matches_played=0),
            PlayerModeStats(player_id="P001", game_mode=GameMode.DUO,
                            ranking_score=3000, total_kills=0, total_score=0, total_deaths=0, matches_played=0),
        ]
        mock_repo.get_by_game_mode.return_value = (1, [player])
        result = LeaderboardService(mock_repo).get_mode_leaderboard(
            game_mode=GameMode.SOLO, page=1, page_size=20
        )
        assert result.entries[0].ranking_score == 8000  # SOLO only, not 11000


class TestMatchServiceRankingScoreUpdate:

    def test_create_match_updates_ranking_score_formula(self):
        """Ranking Score = (Kills × 1000) + Score - (Deaths × 50)"""
        from app.services.match_service import MatchService
        from app.schemas.match_schema import CreateMatchRequest

        mock_db = MagicMock()
        mock_match_repo = MagicMock()
        mock_match_repo.get_by_id.return_value = None
        mock_player_repo = MagicMock()
        mock_leaderboard_repo = MagicMock()
        mock_suspicious_repo = MagicMock()
        mock_suspicious_repo.get_recent_results_for_player.return_value = []
        mock_player_repo.get_by_id.return_value = MagicMock()

        saved_match = MagicMock()
        saved_match.match_id = "M001"
        saved_match.game_mode = GameMode.SOLO
        saved_match.match_duration_seconds = 300
        saved_match.results = []
        mock_match_repo.create.return_value = saved_match

        service = MatchService(
            mock_db, mock_match_repo, mock_player_repo,
            mock_leaderboard_repo, mock_suspicious_repo
        )
        service.create_match(CreateMatchRequest(
            match_id="M001", game_mode=GameMode.SOLO, match_duration_seconds=300,
            results=[{"player_id": "P001", "ping": 30, "score": 500, "kills": 10, "deaths": 3}]
        ))

        # (10*1000) + 500 - (3*50) = 10350
        mock_leaderboard_repo.add_ranking_score.assert_called_once_with(
            player_id="P001",
            game_mode=GameMode.SOLO,
            score_to_add=10350,
            kills=10, score=500, deaths=3
        )

    def test_create_match_cumulative_ranking_score_per_mode(self):
        """Each match adds to cumulative mode-specific score (not a reset)."""
        from app.services.match_service import MatchService
        from app.schemas.match_schema import CreateMatchRequest

        mock_db = MagicMock()
        mock_match_repo = MagicMock()
        mock_match_repo.get_by_id.return_value = None
        mock_player_repo = MagicMock()
        mock_leaderboard_repo = MagicMock()
        mock_suspicious_repo = MagicMock()
        mock_suspicious_repo.get_recent_results_for_player.return_value = []
        mock_player_repo.get_by_id.return_value = MagicMock()

        saved_match = MagicMock()
        saved_match.match_id = "M002"
        saved_match.game_mode = GameMode.DUO
        saved_match.match_duration_seconds = 200
        saved_match.results = []
        mock_match_repo.create.return_value = saved_match

        service = MatchService(
            mock_db, mock_match_repo, mock_player_repo,
            mock_leaderboard_repo, mock_suspicious_repo
        )
        service.create_match(CreateMatchRequest(
            match_id="M002", game_mode=GameMode.DUO, match_duration_seconds=200,
            results=[
                {"player_id": "P001", "ping": 20, "score": 200, "kills": 5, "deaths": 1},
                {"player_id": "P002", "ping": 25, "score": 150, "kills": 3, "deaths": 2},
            ]
        ))

        assert mock_leaderboard_repo.add_ranking_score.call_count == 2
        calls = {
            c.kwargs["player_id"]: c.kwargs["score_to_add"]
            for c in mock_leaderboard_repo.add_ranking_score.call_args_list
        }
        assert calls["P001"] == 5150   # (5*1000)+200-(1*50)
        assert calls["P002"] == 3050   # (3*1000)+150-(2*50)


class TestLeaderboardRepositoryAddRankingScore:

    @staticmethod
    def _session():
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from app.database.base import Base

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        return sessionmaker(bind=engine, autoflush=False, autocommit=False)()

    def test_add_ranking_score_creates_stats_for_new_player(self):
        from sqlalchemy import select

        from app.models.player_model import Player
        from app.repositories.leaderboard_repository import LeaderboardRepository
        from app.utils.enums import DeviceType

        db = self._session()
        db.add(Player(player_id="P004", region=Region.INDIA, device=DeviceType.PC))
        db.commit()

        repo = LeaderboardRepository(db)
        repo.add_ranking_score("P004", GameMode.SOLO, 1000, 10, 500, 2)
        db.commit()

        stats = db.execute(
            select(PlayerModeStats).where(
                PlayerModeStats.player_id == "P004",
                PlayerModeStats.game_mode == GameMode.SOLO,
            )
        ).scalar_one()
        assert stats.ranking_score == 1000
        assert stats.total_kills == 10
        assert stats.matches_played == 1

    def test_add_ranking_score_updates_existing_stats(self):
        from sqlalchemy import select

        from app.models.player_model import Player
        from app.repositories.leaderboard_repository import LeaderboardRepository
        from app.utils.enums import DeviceType

        db = self._session()
        db.add(Player(player_id="P004", region=Region.INDIA, device=DeviceType.PC))
        db.commit()

        repo = LeaderboardRepository(db)
        repo.add_ranking_score("P004", GameMode.SOLO, 1000, 10, 500, 2)
        db.commit()
        repo.add_ranking_score("P004", GameMode.SOLO, 500, 5, 200, 1)
        db.commit()

        stats = db.execute(
            select(PlayerModeStats).where(
                PlayerModeStats.player_id == "P004",
                PlayerModeStats.game_mode == GameMode.SOLO,
            )
        ).scalar_one()
        assert stats.ranking_score == 1500
        assert stats.total_kills == 15
        assert stats.matches_played == 2

    def test_add_ranking_score_twice_before_commit_does_not_duplicate(self):
        from sqlalchemy import func, select

        from app.models.player_model import Player
        from app.repositories.leaderboard_repository import LeaderboardRepository
        from app.utils.enums import DeviceType

        db = self._session()
        db.add(Player(player_id="P004", region=Region.INDIA, device=DeviceType.PC))
        db.commit()

        repo = LeaderboardRepository(db)
        repo.add_ranking_score("P004", GameMode.SOLO, 1000, 10, 500, 2)
        repo.add_ranking_score("P004", GameMode.SOLO, 500, 5, 200, 1)
        db.commit()

        count = db.execute(
            select(func.count()).select_from(PlayerModeStats).where(
                PlayerModeStats.player_id == "P004",
                PlayerModeStats.game_mode == GameMode.SOLO,
            )
        ).scalar_one()
        assert count == 1
