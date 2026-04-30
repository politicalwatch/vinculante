import unicodedata

from sqlalchemy import func

from vinculante.domain.entities import Match, Proposal, Section, TargetDocument
from .base import BaseRepository


def _normalize(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)
    ).casefold()


class TargetRepository(BaseRepository[TargetDocument]):
    model = TargetDocument

    def get_by_title_contains(self, substr: str) -> TargetDocument | None:
        needle = _normalize(substr)
        for t in self.db.query(TargetDocument).all():
            if needle in _normalize(t.title):
                return t
        return None

    def update_stats(self, target_id: int, stats: dict) -> None:
        target = self.get_by_id(target_id)
        if target:
            target.stats = stats
            self.db.commit()

    def get_all_with_counts(self) -> list[dict]:
        proposal_subq = (
            self.db.query(
                Proposal.target_id,
                func.count(Proposal.id).label("proposal_count"),
            )
            .filter(Proposal.target_id.isnot(None))
            .group_by(Proposal.target_id)
            .subquery()
        )

        match_subq = (
            self.db.query(
                Section.target_id,
                func.count(Match.id).label("match_count"),
            )
            .join(Match, Match.section_id == Section.id)
            .filter(Match.degree.in_(("medio", "alto")))
            .group_by(Section.target_id)
            .subquery()
        )

        rows = (
            self.db.query(
                TargetDocument,
                func.coalesce(proposal_subq.c.proposal_count, 0),
                func.coalesce(match_subq.c.match_count, 0),
            )
            .outerjoin(proposal_subq, proposal_subq.c.target_id == TargetDocument.id)
            .outerjoin(match_subq, match_subq.c.target_id == TargetDocument.id)
            .all()
        )

        return [
            {
                "id": target.id,
                "title": target.title,
                "author": target.author,
                "date": target.date,
                "version": target.version,
                "proposal_count": p_count,
                "match_count": m_count,
            }
            for target, p_count, m_count in rows
        ]
