from fastapi import APIRouter, HTTPException, Query, status

from vinculante.domain.entities import MatchStatus
from vinculante.presentation.api.deps import MatchRepoDep
from vinculante.presentation.api.schemas.match import MatchRead, MatchWithProposalRead

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("", response_model=list[MatchWithProposalRead])
def list_matches(
    repo: MatchRepoDep,
    match_status: str | None = None,
    section_id: int | None = None,
    degree: list[str] | None = Query(default=None),
):
    return repo.list_filtered(
        section_id=section_id,
        degrees=degree,
        status=MatchStatus(match_status) if match_status else None,
    )


@router.get("/counts", response_model=dict[int, int])
def count_matches_by_section(
    repo: MatchRepoDep,
    target_id: int,
    degree: list[str] | None = Query(default=None),
):
    return repo.count_by_section_for_target(target_id=target_id, degrees=degree)


@router.get("/{match_id}", response_model=MatchRead)
def get_match(match_id: int, repo: MatchRepoDep):
    match = repo.get_by_id(match_id)
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    return match
