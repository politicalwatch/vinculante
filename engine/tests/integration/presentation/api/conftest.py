from collections.abc import Generator
from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from vinculante.domain.entities import Match, Proposal, Section, TargetDocument
from vinculante.infrastructure.db.session import get_db
from vinculante.main import create_app


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient]:
    """API client bound to the test database session.

    Not used as a context manager, so the lifespan (Redis cache init) does not run.
    """
    app = create_app()

    def _get_test_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_test_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@dataclass
class Scenario:
    law: TargetDocument
    other: TargetDocument
    empty: TargetDocument
    law_proposal_ids: set[int]
    other_proposal_ids: set[int]


@pytest.fixture
def scenario(db_session: Session) -> Scenario:
    """Three targets whose counts all differ, so a wrong filter shows up in the numbers.

    law:   matchable s1, s2, s4 + non-matchable s3; proposals p1, p2, p3
           p1-s1 alto, p1-s2 medio, p2-s1 medio, p3-s4 bajo
           → articles 3, touched 2 (s1, s2), proposals 3, incorporated 2 (p1, p2)
    other: one section and one proposal with an alto match → all counts 1
    empty: nothing → all counts 0
    """
    law = TargetDocument(title="Ley de prueba", author="Gobierno", topic="digitales")
    other = TargetDocument(title="Otra ley", author="Gobierno", topic="clima")
    empty = TargetDocument(title="Ley vacía", author="Gobierno")
    db_session.add_all([law, other, empty])
    db_session.flush()

    s1, s2, s4 = (Section(text=f"artículo {n}", target_id=law.id) for n in (1, 2, 4))
    s3 = Section(text="preámbulo", target_id=law.id, is_matchable=False)
    p1, p2, p3 = (Proposal(text=f"propuesta {n}", target_id=law.id) for n in (1, 2, 3))
    other_section = Section(text="artículo único", target_id=other.id)
    other_proposal = Proposal(text="propuesta única", target_id=other.id)
    db_session.add_all([s1, s2, s3, s4, p1, p2, p3, other_section, other_proposal])
    db_session.flush()

    db_session.add_all([
        Match(proposal_id=p1.id, section_id=s1.id, degree="alto"),
        Match(proposal_id=p1.id, section_id=s2.id, degree="medio"),
        Match(proposal_id=p2.id, section_id=s1.id, degree="medio"),
        Match(proposal_id=p3.id, section_id=s4.id, degree="bajo"),
        Match(proposal_id=other_proposal.id, section_id=other_section.id, degree="alto"),
    ])
    db_session.commit()

    return Scenario(
        law=law,
        other=other,
        empty=empty,
        law_proposal_ids={p1.id, p2.id, p3.id},
        other_proposal_ids={other_proposal.id},
    )
