from fastapi import APIRouter, HTTPException, status

from vinculante.application.stats.target_stats import compute_target_stats
from vinculante.presentation.api.deps import MatchRepoDep, ProposalRepoDep, SectionRepoDep, TargetRepoDep
from vinculante.presentation.api.schemas.target import TargetDocumentRead

router = APIRouter(prefix="/targets", tags=["targets"])


@router.get("", response_model=list[TargetDocumentRead])
def list_targets(repo: TargetRepoDep):
    return repo.get_all_with_counts()


@router.get("/{target_id}", response_model=TargetDocumentRead)
def get_target(
    target_id: int,
    repo: TargetRepoDep,
    section_repo: SectionRepoDep,
    match_repo: MatchRepoDep,
    proposal_repo: ProposalRepoDep,
):
    target = repo.get_by_id(target_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found")
    if target.stats is None:
        sections = section_repo.get_by_target(target_id)
        matches = match_repo.get_accepted_by_target(target_id)
        total_proposals = len(proposal_repo.get_by_target(target_id))
        target.stats = compute_target_stats(sections, matches, total_proposals=total_proposals)
        repo.update_stats(target_id, target.stats)
    return target
