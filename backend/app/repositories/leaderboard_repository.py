from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.player_model import Player, PlayerModeStats
from app.utils.enums import GameMode, Region


class LeaderboardRepository:
    def __init__(self, db: Session):
        self.db = db
        self._cached_mode_stats: dict[tuple[str, GameMode], PlayerModeStats] = {}

    def _find_pending_mode_stats(self, player_id: str, game_mode: GameMode) -> PlayerModeStats | None:
        for obj in self.db.new:
            if (
                isinstance(obj, PlayerModeStats)
                and obj.player_id == player_id
                and obj.game_mode == game_mode
            ):
                return obj
        return None

    def _get_global_query(self):
        return (
            select(Player)
            .join(Player.mode_stats)
            .group_by(Player.player_id)
            .order_by(
                func.sum(PlayerModeStats.ranking_score).desc(),
                func.sum(PlayerModeStats.total_kills).desc(),
                func.sum(PlayerModeStats.total_score).desc(),
                func.sum(PlayerModeStats.total_deaths).asc()
            )
        )

    def get_global(self, offset: int, limit: int) -> tuple[int, list[Player]]:
        count_stmt = select(func.count()).select_from(self._get_global_query().subquery())
        total = self.db.execute(count_stmt).scalar_one()

        players_stmt = (
            self._get_global_query()
            .options(selectinload(Player.mode_stats))
            .offset(offset)
            .limit(limit)
        )
        players = self.db.execute(players_stmt).scalars().all()

        return total, players

    def _get_region_query(self, region: Region):
        return (
            select(Player)
            .join(Player.mode_stats)
            .where(Player.region == region)
            .group_by(Player.player_id)
            .order_by(
                func.sum(PlayerModeStats.ranking_score).desc(),
                func.sum(PlayerModeStats.total_kills).desc(),
                func.sum(PlayerModeStats.total_score).desc(),
                func.sum(PlayerModeStats.total_deaths).asc()
            )
        )

    def get_by_region(self, region: Region, offset: int, limit: int) -> tuple[int, list[Player]]:
        count_stmt = select(func.count()).select_from(self._get_region_query(region).subquery())
        total = self.db.execute(count_stmt).scalar_one()

        players_stmt = (
            self._get_region_query(region)
            .options(selectinload(Player.mode_stats))
            .offset(offset)
            .limit(limit)
        )
        players = self.db.execute(players_stmt).scalars().all()

        return total, players

    def _get_mode_query(self, game_mode: GameMode):
        return (
            select(Player)
            .join(PlayerModeStats, Player.player_id == PlayerModeStats.player_id)
            .where(PlayerModeStats.game_mode == game_mode)
            .order_by(
                PlayerModeStats.ranking_score.desc(),
                PlayerModeStats.total_kills.desc(),
                PlayerModeStats.total_score.desc(),
                PlayerModeStats.total_deaths.asc()
            )
        )

    def get_by_game_mode(self, game_mode: GameMode, offset: int, limit: int) -> tuple[int, list[Player]]:
        count_stmt = select(func.count()).select_from(self._get_mode_query(game_mode).subquery())
        total = self.db.execute(count_stmt).scalar_one()

        players_stmt = (
            self._get_mode_query(game_mode)
            .options(selectinload(Player.mode_stats))
            .offset(offset)
            .limit(limit)
        )
        players = self.db.execute(players_stmt).scalars().all()

        return total, players

    def _get_region_mode_query(self, region: Region, game_mode: GameMode):
        return (
            select(Player)
            .join(PlayerModeStats, Player.player_id == PlayerModeStats.player_id)
            .where(
                Player.region == region,
                PlayerModeStats.game_mode == game_mode
            )
            .order_by(
                PlayerModeStats.ranking_score.desc(),
                PlayerModeStats.total_kills.desc(),
                PlayerModeStats.total_score.desc(),
                PlayerModeStats.total_deaths.asc()
            )
        )

    def get_by_region_and_mode(
        self, region: Region, game_mode: GameMode, offset: int, limit: int
    ) -> tuple[int, list[Player]]:
        count_stmt = select(func.count()).select_from(
            self._get_region_mode_query(region, game_mode).subquery()
        )
        total = self.db.execute(count_stmt).scalar_one()

        players_stmt = (
            self._get_region_mode_query(region, game_mode)
            .options(selectinload(Player.mode_stats))
            .offset(offset)
            .limit(limit)
        )
        players = self.db.execute(players_stmt).scalars().all()

        return total, players

    def get_or_create_mode_stats(self, player_id: str, game_mode: GameMode) -> PlayerModeStats:
        key = (player_id, game_mode)
        if key in self._cached_mode_stats:
            return self._cached_mode_stats[key]

        stats = self._find_pending_mode_stats(player_id, game_mode)
        if stats is None:
            stmt = select(PlayerModeStats).where(
                PlayerModeStats.player_id == player_id,
                PlayerModeStats.game_mode == game_mode
            )
            stats = self.db.execute(stmt).scalar_one_or_none()

        if stats is None:
            stats = PlayerModeStats(
                player_id=player_id,
                game_mode=game_mode,
                ranking_score=0,
                total_kills=0,
                total_score=0,
                total_deaths=0,
                matches_played=0
            )
            self.db.add(stats)

        self._cached_mode_stats[key] = stats
        return stats

    def add_ranking_score(
        self, player_id: str, game_mode: GameMode,
        score_to_add: int, kills: int, score: int, deaths: int
    ) -> None:
        stats = self.get_or_create_mode_stats(player_id, game_mode)
        stats.ranking_score += score_to_add
        stats.total_kills += kills
        stats.total_score += score
        stats.total_deaths += deaths
        stats.matches_played += 1
