import datetime

from pydantic import BaseModel


class TargetDocumentBase(BaseModel):
    title: str
    author: str
    date: datetime.date | None = None
    version: str | None = None


class TargetDocumentRead(TargetDocumentBase):
    id: int
    proposal_count: int = 0
    match_count: int = 0
    stats: dict | None = None

    model_config = {"from_attributes": True}
