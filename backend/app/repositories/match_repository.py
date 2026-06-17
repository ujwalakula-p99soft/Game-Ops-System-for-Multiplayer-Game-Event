from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.match_model import Match, MatchResult


class MatchRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, match: Match, results: list[MatchResult]) -> Match:
        self.db.add(match)
        for result in results:
            self.db.add(result)
        return match

    def get_by_id(self, match_id: str) -> Match | None:
        stmt = (
            select(Match)
            .where(Match.match_id == match_id)
            .options(selectinload(Match.results))
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()
