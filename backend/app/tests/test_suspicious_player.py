from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.dependencies import get_suspicious_player_service
from app.models.player_model import Player
from app.models.match_model import MatchResult
from app.models.suspicious_player_model import SuspiciousPlayer
from app.schemas.suspicious_player_schema import (
    SuspiciousPlayerResponse,
    SuspiciousPlayersResponse
)
from app.services.suspicious_player_service import SuspiciousPlayerService
from app.utils.enums import DeviceType, Region
from app.utils.stats import (
    AggregatedMetrics,
    PlayerMatchMetrics,
    aggregate_metrics,
    compute_anomaly_score,
    compute_match_metrics,
    compute_mean,
    compute_std,
    compute_z_score
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


def _make_result(
    player_id: str = "P001",
    match_id: str = "M001",
    kills: int = 5,
    score: int = 200,
    deaths: int = 2
) -> MatchResult:
    return MatchResult(
        id=1, match_id=match_id, player_id=player_id,
        ping=30, score=score, kills=kills, deaths=deaths
    )


def _make_suspicious_player(
    player_id: str = "P001",
    anomaly_score: float = 3.5
) -> SuspiciousPlayer:
    return SuspiciousPlayer(
        player_id=player_id,
        anomaly_score=anomaly_score,
        avg_kill_efficiency=0.1,
        avg_score_efficiency=1.0,
        avg_kd_ratio=2.5,
        matches_evaluated=5,
        flagged_at=datetime(2024, 6, 1)
    )


client = TestClient(app)


class TestGetSuspiciousPlayersEndpoint:

    def test_returns_200_with_empty_list(self):
        mock_service = MagicMock()
        mock_service.get_suspicious_players.return_value = (
            SuspiciousPlayersResponse(total=0, entries=[])
        )
        app.dependency_overrides[get_suspicious_player_service] = lambda: mock_service

        response = client.get("/suspicious-players")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["entries"] == []
        app.dependency_overrides.clear()

    def test_returns_flagged_players(self):
        mock_service = MagicMock()
        mock_service.get_suspicious_players.return_value = SuspiciousPlayersResponse(
            total=1,
            entries=[
                SuspiciousPlayerResponse(
                    player_id="P001", anomaly_score=3.5,
                    avg_kill_efficiency=0.1, avg_score_efficiency=1.0,
                    avg_kd_ratio=2.5, matches_evaluated=5,
                    flagged_at=datetime(2024, 6, 1)
                )
            ]
        )
        app.dependency_overrides[get_suspicious_player_service] = lambda: mock_service

        response = client.get("/suspicious-players")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["entries"][0]["player_id"] == "P001"
        assert data["entries"][0]["anomaly_score"] == 3.5
        app.dependency_overrides.clear()


class TestStatsUtility:

    def test_compute_match_metrics_standard(self):
        m = compute_match_metrics(kills=10, score=500, deaths=2, match_duration_seconds=100)
        assert m.kill_efficiency == pytest.approx(0.1)
        assert m.score_efficiency == pytest.approx(5.0)
        assert m.kd_ratio == pytest.approx(5.0)

    def test_compute_match_metrics_zero_deaths_uses_one(self):
        m = compute_match_metrics(kills=10, score=500, deaths=0, match_duration_seconds=100)
        assert m.kd_ratio == pytest.approx(10.0)

    def test_compute_match_metrics_zero_duration_uses_one(self):
        m = compute_match_metrics(kills=10, score=500, deaths=2, match_duration_seconds=0)
        assert m.kill_efficiency == pytest.approx(10.0)
        assert m.score_efficiency == pytest.approx(500.0)

    def test_aggregate_metrics_averages_correctly(self):
        m1 = PlayerMatchMetrics(kill_efficiency=0.1, score_efficiency=1.0, kd_ratio=2.0)
        m2 = PlayerMatchMetrics(kill_efficiency=0.3, score_efficiency=3.0, kd_ratio=4.0)
        agg = aggregate_metrics([m1, m2])
        assert agg.avg_kill_efficiency == pytest.approx(0.2)
        assert agg.avg_score_efficiency == pytest.approx(2.0)
        assert agg.avg_kd_ratio == pytest.approx(3.0)

    def test_compute_mean(self):
        assert compute_mean([1.0, 2.0, 3.0]) == pytest.approx(2.0)

    def test_compute_mean_empty_returns_zero(self):
        assert compute_mean([]) == 0.0

    def test_compute_std_population(self):
        # compute_std uses sample std (Bessel's correction n-1)
        # For [2,4,4,4,5,5,7,9]: sample std ≈ 2.138
        values = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
        assert compute_std(values) == pytest.approx(2.138, rel=1e-2)

    def test_compute_std_single_value_returns_zero(self):
        assert compute_std([5.0]) == 0.0

    def test_compute_std_empty_returns_zero(self):
        assert compute_std([]) == 0.0

    def test_compute_z_score_standard(self):
        assert compute_z_score(value=7.0, mean=5.0, std=2.0) == pytest.approx(1.0)

    def test_compute_z_score_zero_std_returns_zero(self):
        assert compute_z_score(value=7.0, mean=5.0, std=0.0) == 0.0

    def test_compute_anomaly_score_empty_pool_returns_zero(self):
        player_agg = AggregatedMetrics(
            avg_kill_efficiency=0.5, avg_score_efficiency=5.0, avg_kd_ratio=3.0
        )
        assert compute_anomaly_score(player_agg, []) == 0.0

    def test_compute_anomaly_score_normal_player_low_score(self):
        pool = [
            AggregatedMetrics(avg_kill_efficiency=0.1, avg_score_efficiency=1.0, avg_kd_ratio=2.0),
            AggregatedMetrics(avg_kill_efficiency=0.1, avg_score_efficiency=1.0, avg_kd_ratio=2.0),
            AggregatedMetrics(avg_kill_efficiency=0.12, avg_score_efficiency=1.1, avg_kd_ratio=2.1),
        ]
        player_agg = AggregatedMetrics(
            avg_kill_efficiency=0.11, avg_score_efficiency=1.05, avg_kd_ratio=2.05
        )
        assert compute_anomaly_score(player_agg, pool) < 2.0

    def test_compute_anomaly_score_outlier_player_high_score(self):
        pool = [
            AggregatedMetrics(avg_kill_efficiency=0.05, avg_score_efficiency=0.5, avg_kd_ratio=1.0)
            for _ in range(10)
        ] + [
            AggregatedMetrics(avg_kill_efficiency=0.06, avg_score_efficiency=0.55, avg_kd_ratio=1.1)
        ]
        player_agg = AggregatedMetrics(
            avg_kill_efficiency=5.0, avg_score_efficiency=50.0, avg_kd_ratio=100.0
        )
        assert compute_anomaly_score(player_agg, pool) > 2.0


class TestSuspiciousPlayerService:

    def _make_service(
        self,
        suspicious_repo: MagicMock | None = None,
        player_repo: MagicMock | None = None
    ) -> SuspiciousPlayerService:
        return SuspiciousPlayerService(
            suspicious_player_repository=suspicious_repo or MagicMock(),
            player_repository=player_repo or MagicMock()
        )

    def test_evaluate_player_skipped_when_insufficient_matches(self):
        suspicious_repo = MagicMock()
        suspicious_repo.get_recent_results_for_player.return_value = [_make_result()]
        service = self._make_service(suspicious_repo=suspicious_repo)

        service.evaluate_player("P001")

        suspicious_repo.upsert_suspicious_player.assert_not_called()
        suspicious_repo.remove_suspicious_player.assert_not_called()

    def test_single_abnormal_match_not_flagged(self):
        """Only 1 result → below MIN_MATCHES_REQUIRED=3 → no flag."""
        suspicious_repo = MagicMock()
        suspicious_repo.get_recent_results_for_player.return_value = [
            _make_result(kills=999, score=99999, deaths=0)
        ]
        service = self._make_service(suspicious_repo=suspicious_repo)

        service.evaluate_player("P001")

        suspicious_repo.upsert_suspicious_player.assert_not_called()

    def test_evaluate_player_clears_when_anomaly_score_below_threshold(self):
        results = [
            _make_result(match_id=f"M00{i}", kills=5, score=200, deaths=2)
            for i in range(5)
        ]
        suspicious_repo = MagicMock()
        suspicious_repo.get_recent_results_for_player.return_value = results
        suspicious_repo.get_match_duration.return_value = 300
        suspicious_repo.get_players_in_pool.return_value = []
        player_repo = MagicMock()
        player_repo.get_by_id.return_value = _make_player()
        service = self._make_service(suspicious_repo=suspicious_repo, player_repo=player_repo)

        service.evaluate_player("P001")

        suspicious_repo.remove_suspicious_player.assert_called_once_with("P001")
        suspicious_repo.upsert_suspicious_player.assert_not_called()

    def test_multiple_abnormal_matches_flagged(self):
        """Player with outlier stats across ≥3 matches vs pool → flagged."""
        # Pool players have normal but slightly varied stats so std > 0
        pool_normal_batches = [
            [_make_result(match_id=f"N{i}_{j}", kills=2 + j, score=50 + j * 5, deaths=5)
             for i in range(5)]
            for j in range(5)
        ]
        outlier_results = [
            _make_result(match_id=f"M{i}", kills=999, score=99999, deaths=0)
            for i in range(5)
        ]
        pool_players = [
            _make_player(f"P{i:03}", Region.INDIA, DeviceType.PC)
            for i in range(2, 7)
        ]
        pool_ids = [p.player_id for p in pool_players]
        # Map each pool player to a different normal-but-varied result set
        pool_results_by_pid = {
            pid: pool_normal_batches[idx]
            for idx, pid in enumerate(pool_ids)
        }
        suspicious_repo = MagicMock()
        suspicious_repo.get_recent_results_for_player.side_effect = (
            lambda player_id, limit: outlier_results if player_id == "P001" else []
        )
        suspicious_repo.get_match_duration.return_value = 60
        suspicious_repo.get_players_in_pool.return_value = pool_players
        # Real dict with varied pool data so std > 0 and z-scores are meaningful
        suspicious_repo.get_pool_player_results_batch.return_value = pool_results_by_pid
        player_repo = MagicMock()
        player_repo.get_by_id.return_value = _make_player()
        service = self._make_service(suspicious_repo=suspicious_repo, player_repo=player_repo)

        service.evaluate_player("P001")

        suspicious_repo.upsert_suspicious_player.assert_called_once()
        flagged = suspicious_repo.upsert_suspicious_player.call_args[0][0]
        assert flagged.player_id == "P001"
        assert flagged.anomaly_score >= 2.0

    def test_get_suspicious_players_returns_all_from_repo(self):
        suspicious_repo = MagicMock()
        suspicious_repo.get_all.return_value = [
            _make_suspicious_player("P001", 3.5),
            _make_suspicious_player("P002", 2.8)
        ]
        service = self._make_service(suspicious_repo=suspicious_repo)

        result = service.get_suspicious_players()

        assert result.total == 2
        assert result.entries[0].player_id == "P001"
        assert result.entries[1].player_id == "P002"

    def test_evaluate_player_uses_min_matches_required(self):
        suspicious_repo = MagicMock()
        suspicious_repo.get_recent_results_for_player.return_value = (
            [_make_result()] * (SuspiciousPlayerService.MIN_MATCHES_REQUIRED - 1)
        )
        service = self._make_service(suspicious_repo=suspicious_repo)

        service.evaluate_player("P001")

        suspicious_repo.upsert_suspicious_player.assert_not_called()
        suspicious_repo.remove_suspicious_player.assert_not_called()

    def test_evaluate_player_proceeds_at_min_matches_threshold(self):
        results = [
            _make_result(match_id=f"M{i}")
            for i in range(SuspiciousPlayerService.MIN_MATCHES_REQUIRED)
        ]
        suspicious_repo = MagicMock()
        suspicious_repo.get_recent_results_for_player.return_value = results
        suspicious_repo.get_match_duration.return_value = 300
        suspicious_repo.get_players_in_pool.return_value = []
        player_repo = MagicMock()
        player_repo.get_by_id.return_value = _make_player()
        service = self._make_service(suspicious_repo=suspicious_repo, player_repo=player_repo)

        service.evaluate_player("P001")

        suspicious_repo.remove_suspicious_player.assert_called_once()
