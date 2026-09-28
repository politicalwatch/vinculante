import datetime

from pydantic import BaseModel


class TargetDocumentBase(BaseModel):
    title: str
    author: str
    date: datetime.date | None = None
    version: str | None = None


class TargetListItemRead(TargetDocumentBase):
    id: int
    articles: int = 0  # matchable sections
    touched: int = 0  # matchable sections with at least one alto/medio match
    proposals: int = 0
    incorporated: int = 0  # proposals with at least one alto/medio match


class TargetDocumentRead(TargetDocumentBase):
    id: int
    stats: dict | None = None
    summary: str | None = None

    model_config = {"from_attributes": True}
