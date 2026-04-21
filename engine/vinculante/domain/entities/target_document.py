import datetime

from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class TargetDocument(Base):
    __tablename__ = "target_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    author: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[datetime.date | None] = mapped_column(Date)
    version: Mapped[str | None] = mapped_column(String)

    sections: Mapped[list["Section"]] = relationship(back_populates="target_document")
