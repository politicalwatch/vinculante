import pandas as pd

from vinculante.domain.entities import MatchStatus
from vinculante.domain.ports.repositories import MatchRepositoryProtocol


def _section_title(text: str | None) -> str | None:
    if not text:
        return None
    return text.split("\n", 1)[0].lstrip("#").strip() or None


class MatchExporter:
    def __init__(self, match_repo: MatchRepositoryProtocol) -> None:
        self.match_repo = match_repo

    def _build_dataframe(
        self,
        status: MatchStatus | None = None,
        include_rejected: bool = False,
        target_id: int | None = None,
    ) -> pd.DataFrame:
        if target_id is not None:
            matches = self.match_repo.get_by_target(target_id)
            if status:
                matches = [m for m in matches if m.status == status]
        elif status:
            matches = self.match_repo.get_by_status(status)
        else:
            matches = self.match_repo.get_all()
        if not include_rejected:
            matches = [m for m in matches if m.degree != "ninguno"]
        df = pd.DataFrame([
            {
                "section_id": m.section_id,
                "section_title": _section_title(m.section.text) if m.section else None,
                "proposal_id": m.proposal_id,
                "proposal_text": m.proposal.text if m.proposal else None,
                "match_id": m.id,
                "degree": m.degree,
                "confidence": m.confidence,
                "status": m.status.value if m.status else None,
                "explanation": m.explanation,
            }
            for m in matches
        ])
        if not df.empty:
            df.sort_values(["section_id", "proposal_id", "match_id"], inplace=True, ignore_index=True)
        return df

    def export_to_csv(
        self,
        output_path: str,
        status: MatchStatus | None = None,
        include_rejected: bool = False,
        target_id: int | None = None,
    ) -> int:
        df = self._build_dataframe(status=status, include_rejected=include_rejected, target_id=target_id)
        df.to_csv(output_path, index=False)
        return len(df)

    def export_to_xlsx(
        self,
        output_path: str,
        status: MatchStatus | None = None,
        include_rejected: bool = False,
        target_id: int | None = None,
    ) -> int:
        df = self._build_dataframe(status=status, include_rejected=include_rejected, target_id=target_id)
        df.to_excel(output_path, index=False)
        return len(df)
