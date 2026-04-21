from pydantic import BaseModel


class ProposalBase(BaseModel):
    text: str
    author: str | None = None
    author_type: str | None = None
    reference: str | None = None
    topic: str | None = None
    subtopic: str | None = None
    source_file: str | None = None


class ProposalRead(ProposalBase):
    id: int

    model_config = {"from_attributes": True}
