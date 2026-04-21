from vinculante.domain.entities import Section, TargetDocument
from vinculante.domain.ports.chunking import ChunkerProtocol
from vinculante.domain.ports.repositories import SectionRepositoryProtocol, TargetRepositoryProtocol


class TargetIngestor:
    def __init__(
        self,
        target_repo: TargetRepositoryProtocol,
        section_repo: SectionRepositoryProtocol,
        chunker: ChunkerProtocol,
    ) -> None:
        self.target_repo = target_repo
        self.section_repo = section_repo
        self.chunker = chunker

    def ingest(
        self,
        file_path: str,
        title: str,
        author: str,
        version: str | None = None,
    ) -> TargetDocument:
        target = TargetDocument(title=title, author=author, version=version)
        target = self.target_repo.save(target)

        chunks = self.chunker.chunk(file_path)
        sections = [
            Section(
                text=chunk["text"],
                plain_text=chunk["text"],
                page_number=chunk.get("metadata", {}).get("page_number"),
                section_type=chunk.get("metadata", {}).get("dl_meta", {}).get("doc_items", [{}])[0].get("label"),
                target_id=target.id,
            )
            for chunk in chunks
        ]
        self.section_repo.bulk_save(sections)
        return target
