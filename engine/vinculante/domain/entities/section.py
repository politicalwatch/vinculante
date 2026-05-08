from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

if TYPE_CHECKING:
    from .match import Match
    from .target_document import TargetDocument


class Section(Base):
    __tablename__ = "sections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(String, nullable=False)
    text_markdown: Mapped[str | None] = mapped_column(String)
    clear_language: Mapped[str | None] = mapped_column(String)
    page_number: Mapped[int | None] = mapped_column(Integer)
    section_type: Mapped[str | None] = mapped_column(String)
    section_number: Mapped[str | None] = mapped_column(String)
    meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_matchable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("sections.id"))
    target_id: Mapped[int] = mapped_column(ForeignKey("target_documents.id"), nullable=False)
    embedding = mapped_column(Vector(None))

    parent: Mapped["Section | None"] = relationship(remote_side="Section.id")
    children: Mapped[list["Section"]] = relationship(back_populates="parent")
    target_document: Mapped["TargetDocument"] = relationship(back_populates="sections")
    matches: Mapped[list["Match"]] = relationship(back_populates="section")
