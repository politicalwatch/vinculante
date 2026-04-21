from vinculante.domain.entities import Proposal
from .base import BaseRepository


class ProposalRepository(BaseRepository[Proposal]):
    model = Proposal
