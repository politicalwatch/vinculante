from fastapi import APIRouter

from vinculante.presentation.api.deps import TargetRepoDep
from vinculante.presentation.api.schemas.viz import VizTargetSignatureRead

router = APIRouter(prefix="/viz_api", tags=["viz"])


@router.get("/targets", response_model=list[VizTargetSignatureRead])
def list_target_signatures(repo: TargetRepoDep):
    return repo.get_all_signatures()
