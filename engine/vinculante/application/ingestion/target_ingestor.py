import unicodedata

from vinculante.domain.entities import Section, TargetDocument
from vinculante.domain.ports.chunking import ChunkerProtocol
from vinculante.domain.ports.repositories import SectionRepositoryProtocol, TargetRepositoryProtocol


def _normalize(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.casefold().strip()


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

        title_norm = _normalize(title)
        chunks = self.chunker.chunk(file_path)
        sections: list[Section] = []
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            is_heading_only = bool(metadata.get("is_heading_only"))
            if is_heading_only and _normalize(chunk["text"]) == title_norm:
                continue
            raw_meta = metadata.get("dl_meta", {})
            doc_items = raw_meta.get("doc_items", [])
            section_type = doc_items[0].get("label") if doc_items else None
            prov = doc_items[0].get("prov", []) if doc_items else []
            page_number = prov[0].get("page_no") if prov else None
            sections.append(Section(
                text=chunk["text"],
                text_markdown=chunk.get("text_markdown"),
                clear_language=chunk["text"],
                page_number=page_number,
                section_type=section_type,
                meta=raw_meta or None,
                is_matchable=not is_heading_only,
                target_id=target.id,
            ))
        self.section_repo.bulk_save(sections)
        return target
