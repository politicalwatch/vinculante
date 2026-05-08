import logging

from vinculante.domain.entities import Proposal
from vinculante.domain.ports.repositories import ProposalRepositoryProtocol
from vinculante.domain.ports.storage import FileLoaderProtocol

_logger = logging.getLogger(__name__)

_CANONICAL_AUTHOR_TYPES = frozenset({"citizen", "academia", "institution", "government", "ngo"})


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

    def ingest(self, file_path: str, target_id: int | None = None) -> list[Proposal]:
        rows = self.loader.load(file_path)
        proposals = [
            Proposal(
                text=row["text"],
                author=row.get("author") or None,
                author_type=normalize_author_type(row.get("author_type")),
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
