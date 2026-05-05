from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

if TYPE_CHECKING:
    from .match import Match
    from .target_document import TargetDocument


class Proposal(Base):
    __tablename__ = "proposals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(String, nullable=False)
    author: Mapped[str | None] = mapped_column(String)
    author_type: Mapped[str | None] = mapped_column(String)
    reference: Mapped[str | None] = mapped_column(String)
    topic: Mapped[str | None] = mapped_column(String)
    subtopic: Mapped[str | None] = mapped_column(String)
    source_file: Mapped[str | None] = mapped_column(String)
    target_id: Mapped[int | None] = mapped_column(ForeignKey("target_documents.id"))
    embedding = mapped_column(Vector(None))

    target_document: Mapped["TargetDocument | None"] = relationship()
    matches: Mapped[list["Match"]] = relationship(back_populates="proposal")
