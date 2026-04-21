from fastapi import APIRouter, HTTPException, status

from vinculante.presentation.api.deps import SectionRepoDep
from vinculante.presentation.api.schemas.section import SectionRead

router = APIRouter(prefix="/sections", tags=["sections"])


@router.get("", response_model=list[SectionRead])
def list_sections(repo: SectionRepoDep, target_id: int | None = None):
    if target_id is not None:
        return repo.get_by_target(target_id)
    return repo.get_all()


@router.get("/{section_id}", response_model=SectionRead)
def get_section(section_id: int, repo: SectionRepoDep):
    section = repo.get_by_id(section_id)
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")
    return section
