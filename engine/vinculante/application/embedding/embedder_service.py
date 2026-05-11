from tqdm import tqdm

from vinculante.domain.entities import Proposal, Section
from vinculante.domain.ports.embeddings import EmbedderProtocol
from vinculante.domain.ports.repositories import (
    ProposalRepositoryProtocol,
    SectionRepositoryProtocol,
)


class SectionEmbedderService:
    def __init__(
        self,
        section_repo: SectionRepositoryProtocol,
        embedder: EmbedderProtocol,
        batch_size: int = 50,
    ) -> None:
        self.section_repo = section_repo
        self.embedder = embedder
        self.batch_size = batch_size

    def embed_sections(self, target_id: int | None = None) -> int:
        sections = (
            self.section_repo.get_by_target(target_id)
            if target_id
            else self.section_repo.get_all()
        )
        unembedded = [s for s in sections if s.embedding is None and s.is_matchable]
        if not unembedded:
            return 0

        total = 0
        for i in tqdm(range(0, len(unembedded), self.batch_size), desc="Embedding sections"):
            batch: list[Section] = unembedded[i : i + self.batch_size]
            texts = [s.clear_language or s.text for s in batch]
            embeddings = self.embedder.embed_documents(texts)
            for section, embedding in zip(batch, embeddings, strict=True):
                section.embedding = embedding
            self.section_repo.bulk_save(batch)
            total += len(batch)

        return total


class ProposalEmbedderService:
    def __init__(
        self,
        proposal_repo: ProposalRepositoryProtocol,
        embedder: EmbedderProtocol,
        batch_size: int = 50,
    ) -> None:
        self.proposal_repo = proposal_repo
        self.embedder = embedder
        self.batch_size = batch_size

    def embed_proposals(self, source_file: str | None = None, target_id: int | None = None) -> int:
        if source_file and target_id:
            raise ValueError("source_file and target_id are mutually exclusive")
        if target_id:
            proposals = self.proposal_repo.get_by_target(target_id)
        elif source_file:
            proposals = self.proposal_repo.get_by_source_file(source_file)
        else:
            proposals = self.proposal_repo.get_all()
        unembedded = [p for p in proposals if p.embedding is None]
        if not unembedded:
            return 0

        total = 0
        for i in tqdm(range(0, len(unembedded), self.batch_size), desc="Embedding proposals"):
            batch: list[Proposal] = unembedded[i : i + self.batch_size]
            embeddings = self.embedder.embed_documents([p.text for p in batch])
            for proposal, embedding in zip(batch, embeddings, strict=True):
                proposal.embedding = embedding
            self.proposal_repo.bulk_save(batch)
            total += len(batch)

        return total
