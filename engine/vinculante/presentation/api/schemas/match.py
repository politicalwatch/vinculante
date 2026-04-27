from pydantic import BaseModel

from vinculante.domain.entities import MatchStatus
from .proposal import ProposalRead


class MatchRead(BaseModel):
    id: int
    proposal_id: int
    section_id: int
    degree: str | None = None
    explanation: str | None = None
    confidence: float | None = None
    status: MatchStatus
    section_spans: list | None = None

    model_config = {"from_attributes": True}


class MatchWithProposalRead(MatchRead):
    proposal: ProposalRead


