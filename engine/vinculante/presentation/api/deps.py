from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from vinculante.infrastructure.config.settings import Settings, get_settings
from vinculante.infrastructure.db.session import get_db
from vinculante.infrastructure.db.repositories.matches import MatchRepository
from vinculante.infrastructure.db.repositories.proposals import ProposalRepository
from vinculante.infrastructure.db.repositories.sections import SectionRepository
from vinculante.infrastructure.db.repositories.targets import TargetRepository

db_dependency = Annotated[Session, Depends(get_db)]
settings_dependency = Annotated[Settings, Depends(get_settings)]


def get_proposal_repo(db: db_dependency) -> ProposalRepository:
    return ProposalRepository(db)


def get_section_repo(db: db_dependency) -> SectionRepository:
    return SectionRepository(db)


def get_match_repo(db: db_dependency) -> MatchRepository:
    return MatchRepository(db)


def get_target_repo(db: db_dependency) -> TargetRepository:
    return TargetRepository(db)


ProposalRepoDep = Annotated[ProposalRepository, Depends(get_proposal_repo)]
SectionRepoDep = Annotated[SectionRepository, Depends(get_section_repo)]
MatchRepoDep = Annotated[MatchRepository, Depends(get_match_repo)]
TargetRepoDep = Annotated[TargetRepository, Depends(get_target_repo)]
