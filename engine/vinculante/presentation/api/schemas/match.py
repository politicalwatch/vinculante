from pydantic import BaseModel

from vinculante.domain.entities import MatchStatus


class MatchRead(BaseModel):
    id: int
    proposal_id: int
    section_id: int
    degree: str | None = None
    explanation: str | None = None
    confidence: float | None = None
    status: MatchStatus
    section_start_at: int | None = None
    section_end_at: int | None = None

    model_config = {"from_attributes": True}


