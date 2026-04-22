from vinculante.domain.entities import Proposal
from vinculante.domain.ports.repositories import ProposalRepositoryProtocol
from vinculante.domain.ports.storage import FileLoaderProtocol


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
                author_type=row.get("author_type") or None,
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
