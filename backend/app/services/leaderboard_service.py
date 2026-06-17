from app.models.player_model import Player
from app.schemas.leaderboard_schema import LeaderboardEntryResponse, LeaderboardResponse
from app.repositories.leaderboard_repository import LeaderboardRepository
from app.utils.enums import GameMode, Region
from app.core.logger import logger


class LeaderboardService:
    def __init__(self, leaderboard_repository: LeaderboardRepository):
        self.leaderboard_repository = leaderboard_repository

    @staticmethod
    def _compute_ranking_score(kills: int, score: int, deaths: int) -> int:
        return (kills * 1000) + score - (deaths * 50)

    def _get_total_ranking_score(self, player: Player) -> int:
        return sum(stat.ranking_score for stat in player.mode_stats)

    def _build_entries(self, players: list[Player], offset: int) -> list[LeaderboardEntryResponse]:
        entries = []
        for i, player in enumerate(players):
            score = self._get_total_ranking_score(player)
            entries.append(
                LeaderboardEntryResponse(
                    rank=offset + i + 1,
                    player_id=player.player_id,
                    ranking_score=score,
                    region=player.region
                )
            )
        return entries

    def get_global_leaderboard(self, page: int, page_size: int) -> LeaderboardResponse:
        offset = (page - 1) * page_size
        total, players = self.leaderboard_repository.get_global(offset=offset, limit=page_size)
        logger.info(f"Global leaderboard fetched: page={page}, page_size={page_size}, total={total}")
        return LeaderboardResponse(
            total=total, page=page, page_size=page_size,
            entries=self._build_entries(players, offset)
        )

    def get_region_leaderboard(self, region: Region, page: int, page_size: int) -> LeaderboardResponse:
        offset = (page - 1) * page_size
        total, players = self.leaderboard_repository.get_by_region(
            region=region, offset=offset, limit=page_size
        )
        logger.info(f"Region leaderboard fetched: region={region}, page={page}, page_size={page_size}, total={total}")
        return LeaderboardResponse(
            total=total, page=page, page_size=page_size,
            entries=self._build_entries(players, offset)
        )

    def get_mode_leaderboard(self, game_mode: GameMode, page: int, page_size: int) -> LeaderboardResponse:
        offset = (page - 1) * page_size
        total, players = self.leaderboard_repository.get_by_game_mode(
            game_mode=game_mode, offset=offset, limit=page_size
        )

        def get_mode_score(p: Player) -> int:
            for stat in p.mode_stats:
                if stat.game_mode == game_mode:
                    return stat.ranking_score
            return 0

        entries = [
            LeaderboardEntryResponse(
                rank=offset + i + 1,
                player_id=player.player_id,
                ranking_score=get_mode_score(player),
                region=player.region
            )
            for i, player in enumerate(players)
        ]
        logger.info(f"Mode leaderboard fetched: mode={game_mode}, page={page}, page_size={page_size}, total={total}")
        return LeaderboardResponse(total=total, page=page, page_size=page_size, entries=entries)

    def get_region_mode_leaderboard(
        self, region: Region, game_mode: GameMode, page: int, page_size: int
    ) -> LeaderboardResponse:
        offset = (page - 1) * page_size
        total, players = self.leaderboard_repository.get_by_region_and_mode(
            region=region, game_mode=game_mode, offset=offset, limit=page_size
        )

        def get_mode_score(p: Player) -> int:
            for stat in p.mode_stats:
                if stat.game_mode == game_mode:
                    return stat.ranking_score
            return 0

        entries = [
            LeaderboardEntryResponse(
                rank=offset + i + 1,
                player_id=player.player_id,
                ranking_score=get_mode_score(player),
                region=player.region
            )
            for i, player in enumerate(players)
        ]
        logger.info(
            f"Region+mode leaderboard fetched: region={region}, mode={game_mode}, "
            f"page={page}, page_size={page_size}, total={total}"
        )
        return LeaderboardResponse(total=total, page=page, page_size=page_size, entries=entries)
