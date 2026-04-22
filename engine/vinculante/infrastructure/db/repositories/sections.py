from sqlalchemy import select
from sqlalchemy.orm import Session

from vinculante.domain.entities import Section
from .base import BaseRepository


class SectionRepository(BaseRepository[Section]):
    model = Section

    def get_by_target(self, target_id: int) -> list[Section]:
        return list(self.db.query(Section).filter(Section.target_id == target_id).all())

    def find_similar(
        self,
        embedding: list[float],
        target_id: int,
        k: int = 5,
    ) -> list[Section]:
        stmt = select(Section).filter(Section.embedding.isnot(None))
        stmt = stmt.filter(Section.target_id == target_id)
        stmt = stmt.order_by(Section.embedding.l2_distance(embedding)).limit(k)
        return list(self.db.scalars(stmt).all())
