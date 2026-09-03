import datetime

from pydantic import BaseModel


class VizTargetSignatureRead(BaseModel):
    id: int
    title: str
    author: str
    date: datetime.date | None = None
    version: str | None = None
    articles: int = 0
    touched: int = 0
    proposals: int = 0
    incorporated: int = 0
