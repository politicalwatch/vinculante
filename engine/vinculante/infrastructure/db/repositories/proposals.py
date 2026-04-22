from vinculante.domain.entities import Proposal
from .base import BaseRepository


class ProposalRepository(BaseRepository[Proposal]):
    model = Proposal

    def get_by_source_file(self, source_file: str) -> list[Proposal]:
        return list(self.db.query(Proposal).filter(Proposal.source_file == source_file).all())

    def get_by_target(self, target_id: int) -> list[Proposal]:
        return list(self.db.query(Proposal).filter(Proposal.target_id == target_id).all())
