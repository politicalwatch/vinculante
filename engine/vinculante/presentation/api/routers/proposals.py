from fastapi import APIRouter, HTTPException, status

from vinculante.presentation.api.deps import ProposalRepoDep
from vinculante.presentation.api.schemas.proposal import ProposalRead

router = APIRouter(prefix="/proposals", tags=["proposals"])


@router.get("", response_model=list[ProposalRead])
def list_proposals(repo: ProposalRepoDep):
    return repo.get_all()


@router.get("/{proposal_id}", response_model=ProposalRead)
def get_proposal(proposal_id: int, repo: ProposalRepoDep):
    proposal = repo.get_by_id(proposal_id)
    if not proposal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")
    return proposal
