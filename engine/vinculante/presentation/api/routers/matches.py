from fastapi import APIRouter, HTTPException, status

from vinculante.presentation.api.deps import MatchRepoDep
from vinculante.presentation.api.schemas.match import MatchRead

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("", response_model=list[MatchRead])
def list_matches(repo: MatchRepoDep, match_status: str | None = None):
    if match_status:
        from vinculante.domain.entities import MatchStatus
        return repo.get_by_status(MatchStatus(match_status))
    return repo.get_all()


@router.get("/{match_id}", response_model=MatchRead)
def get_match(match_id: int, repo: MatchRepoDep):
    match = repo.get_by_id(match_id)
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    return match
