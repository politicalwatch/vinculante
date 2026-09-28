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

    def update_summary(self, target_id: int, summary: str) -> None:
        target = self.get_by_id(target_id)
        if target:
            target.summary = summary
            self.db.commit()

    def get_all_with_counts(self) -> list[dict]:
        """Every target with the counts behind its signature: matchable articles,
        how many of them have an accepted (alto/medio) match, proposals, and how
        many of those have an accepted match."""
        accepted = ("alto", "medio")

        article_subq = (
            self.db.query(
                Section.target_id,
                func.count(Section.id).label("articles"),
            )
            .filter(Section.is_matchable.is_(True))
            .group_by(Section.target_id)
            .subquery()
        )

        proposal_subq = (
            self.db.query(
                Proposal.target_id,
                func.count(Proposal.id).label("proposals"),
            )
            .filter(Proposal.target_id.isnot(None))
            .group_by(Proposal.target_id)
            .subquery()
        )

        touched_subq = (
            self.db.query(
                Section.target_id,
                func.count(func.distinct(Section.id)).label("touched"),
            )
            .join(Match, Match.section_id == Section.id)
            .filter(Section.is_matchable.is_(True))
            .filter(Match.degree.in_(accepted))
            .group_by(Section.target_id)
            .subquery()
        )

        incorporated_subq = (
            self.db.query(
                Proposal.target_id,
                func.count(func.distinct(Proposal.id)).label("incorporated"),
            )
            .join(Match, Match.proposal_id == Proposal.id)
            .filter(Proposal.target_id.isnot(None))
            .filter(Match.degree.in_(accepted))
            .group_by(Proposal.target_id)
            .subquery()
        )

        rows = (
            self.db.query(
                TargetDocument,
                func.coalesce(article_subq.c.articles, 0),
                func.coalesce(touched_subq.c.touched, 0),
                func.coalesce(proposal_subq.c.proposals, 0),
                func.coalesce(incorporated_subq.c.incorporated, 0),
            )
            .outerjoin(article_subq, article_subq.c.target_id == TargetDocument.id)
            .outerjoin(touched_subq, touched_subq.c.target_id == TargetDocument.id)
            .outerjoin(proposal_subq, proposal_subq.c.target_id == TargetDocument.id)
            .outerjoin(incorporated_subq, incorporated_subq.c.target_id == TargetDocument.id)
            .order_by(TargetDocument.id.desc())
            .all()
        )

        return [
            {
                "id": target.id,
                "title": target.title,
                "author": target.author,
                "date": target.date,
                "version": target.version,
                "articles": articles,
                "touched": touched,
                "proposals": proposals,
                "incorporated": incorporated,
            }
            for target, articles, touched, proposals, incorporated in rows
        ]
