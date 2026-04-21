from pydantic import BaseModel


class SectionRead(BaseModel):
    id: int
    text: str
    plain_text: str | None = None
    page_number: int | None = None
    section_type: str | None = None
    section_number: str | None = None
    parent_id: int | None = None
    target_id: int

    model_config = {"from_attributes": True}
