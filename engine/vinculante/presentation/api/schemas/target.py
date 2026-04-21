import datetime

from pydantic import BaseModel


class TargetDocumentBase(BaseModel):
    title: str
    author: str
    date: datetime.date | None = None
    version: str | None = None


class TargetDocumentRead(TargetDocumentBase):
    id: int

    model_config = {"from_attributes": True}
