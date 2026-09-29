import logging

from vinculante.domain.entities import Proposal
from vinculante.domain.ports.repositories import ProposalRepositoryProtocol
from vinculante.domain.ports.storage import FileLoaderProtocol

_logger = logging.getLogger(__name__)

_CANONICAL_AUTHOR_TYPES = frozenset({"citizen", "academia", "institution", "government", "ngo"})

# Separates proponents in flat files (CSV/XLSX `author` column, preview CSVs).
# Not a comma: organisation names can contain commas.
AUTHORS_SEPARATOR = ";"


def parse_authors(value: str | list[str] | None) -> list[str]:
    """One item per proponent, stripped, without empties or repeats (order kept)."""
    if not value:
        return []
    parts = value if isinstance(value, list) else value.split(AUTHORS_SEPARATOR)
    authors: list[str] = []
    for part in parts:
        name = part.strip()
        if name and name not in authors:
            authors.append(name)
    return authors


def format_authors(authors: list[str]) -> str:
    """Inverse of `parse_authors`, for writing flat files."""
    return f"{AUTHORS_SEPARATOR} ".join(authors)


def normalize_author_type(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip().lower()
    if normalized in _CANONICAL_AUTHOR_TYPES:
        return normalized
    _logger.warning("Unknown author_type value %r — stored as NULL", value)
    return None


class ProposalIngestor:
    def __init__(
        self,
        repo: ProposalRepositoryProtocol,
        loader: FileLoaderProtocol,
    ) -> None:
        self.repo = repo
        self.loader = loader

    def ingest(
        self,
        file_path: str,
        target_id: int | None = None,
        author_type: str | None = None,
    ) -> list[Proposal]:
        rows = self.loader.load(file_path)
        proposals = [
            Proposal(
                text=row["text"],
                authors=parse_authors(row.get("authors") or row.get("author")),
                author_type=normalize_author_type(row.get("author_type") or author_type),
                reference=row.get("reference") or None,
                topic=row.get("topic") or None,
                subtopic=row.get("subtopic") or None,
                source_file=file_path,
                target_id=target_id,
            )
            for row in rows
            if row.get("text")
        ]
        return self.repo.bulk_save(proposals)
