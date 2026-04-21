from vinculante.domain.entities import Match, MatchStatus
from .base import BaseRepository


class MatchRepository(BaseRepository[Match]):
    model = Match

    def get_by_proposal(self, proposal_id: int) -> list[Match]:
        return list(self.db.query(Match).filter(Match.proposal_id == proposal_id).all())

    def get_by_status(self, status: MatchStatus) -> list[Match]:
        return list(self.db.query(Match).filter(Match.status == status).all())
