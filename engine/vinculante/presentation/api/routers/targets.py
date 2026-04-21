from fastapi import APIRouter, HTTPException, status

from vinculante.presentation.api.deps import TargetRepoDep
from vinculante.presentation.api.schemas.target import TargetDocumentRead

router = APIRouter(prefix="/targets", tags=["targets"])


@router.get("", response_model=list[TargetDocumentRead])
def list_targets(repo: TargetRepoDep):
    return repo.get_all()


@router.get("/{target_id}", response_model=TargetDocumentRead)
def get_target(target_id: int, repo: TargetRepoDep):
    target = repo.get_by_id(target_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found")
    return target
