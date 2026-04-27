from sqlalchemy import func
from sqlalchemy.orm import joinedload

from vinculante.domain.entities import Match, MatchStatus, Proposal, Section
from .base import BaseRepository


class MatchRepository(BaseRepository[Match]):
    model = Match

    def get_by_proposal(self, proposal_id: int) -> list[Match]:
        return list(self.db.query(Match).filter(Match.proposal_id == proposal_id).all())

    def get_by_status(self, status: MatchStatus) -> list[Match]:
        return list(self.db.query(Match).filter(Match.status == status).all())

    def list_filtered(
        self,
        section_id: int | None = None,
        degrees: list[str] | None = None,
        status: MatchStatus | None = None,
    ) -> list[Match]:
        q = self.db.query(Match).options(joinedload(Match.proposal))
        if section_id is not None:
            q = q.filter(Match.section_id == section_id)
        if degrees:
            q = q.filter(Match.degree.in_(degrees))
        if status is not None:
            q = q.filter(Match.status == status)
        return list(q.all())

    def count_by_section_for_target(
        self,
        target_id: int,
        degrees: list[str] | None = None,
    ) -> dict[int, int]:
        q = (
            self.db.query(Match.section_id, func.count(Match.id))
            .join(Section, Match.section_id == Section.id)
            .filter(Section.target_id == target_id)
        )
        if degrees:
            q = q.filter(Match.degree.in_(degrees))
        return {section_id: count for section_id, count in q.group_by(Match.section_id).all()}

    def get_by_target(self, target_id: int) -> list[Match]:
        return list(
            self.db.query(Match)
            .join(Match.proposal)
            .filter(Proposal.target_id == target_id)
            .all()
        )

    def get_accepted_by_target(
        self,
        target_id: int,
        min_confidence: float = 0.0,
        excluded_degrees: tuple[str, ...] = ("ninguno",),
    ) -> list[Match]:
        query = (
            self.db.query(Match)
            .join(Match.proposal)
            .filter(Proposal.target_id == target_id)
            .filter(Match.confidence >= min_confidence)
        )
        if excluded_degrees:
            query = query.filter(Match.degree.notin_(excluded_degrees))
        return list(query.all())
