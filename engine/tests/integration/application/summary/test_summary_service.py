import pytest
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel

from vinculante.application.summary.schemas import (
    DocumentOverview,
    GapAnalysis,
    Highlight,
    HighlightExtraction,
    Synthesis,
    ThematicCluster,
    ThemeAnalysis,
)
from vinculante.application.summary.summary_service import SummaryService
from vinculante.domain.entities import Match, Proposal, Section, TargetDocument
from vinculante.infrastructure.config.settings import Settings
from vinculante.infrastructure.db.repositories.matches import MatchRepository
from vinculante.infrastructure.db.repositories.proposals import ProposalRepository
from vinculante.infrastructure.db.repositories.sections import SectionRepository
from vinculante.infrastructure.db.repositories.targets import TargetRepository


# ---------------------------------------------------------------------------
# FakeStructuredLLM — keyed by schema type, tracks call counts
# ---------------------------------------------------------------------------


class FakeStructuredLLM:
    def __init__(self, responses: dict[type, BaseModel | Exception]) -> None:
        self.calls: dict[type, int] = {}
        self._responses = responses

    def with_structured_output(self, schema, **kwargs):
        fake = self

        async def _fn(_input):
            fake.calls[schema] = fake.calls.get(schema, 0) + 1
            r = fake._responses.get(schema)
            if isinstance(r, Exception):
                raise r
            if r is None:
                raise KeyError(f"no fake response configured for {schema!r}")
            return r

        return RunnableLambda(_fn)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _settings(**overrides) -> Settings:
    base = dict(
        db_url="postgresql+psycopg2://x:x@localhost/x",
        cache_redis_host="redis://localhost",
        summary_prompt_version="v1",
    )
    return Settings(**{**base, **overrides})


def _make_target(db_session, title: str = "Test Doc") -> TargetDocument:
    return TargetRepository(db_session).save(TargetDocument(title=title, author="author"))


def _embed(embedder: DeterministicFakeEmbedding, text: str) -> list[float]:
    return embedder.embed_query(text)


def _full_responses() -> dict[type, BaseModel]:
    return {
        DocumentOverview: DocumentOverview(intro="overview intro", axes=["eje 1"]),
        ThemeAnalysis: ThemeAnalysis(clusters=[ThematicCluster(label="Vivienda", description="desc")]),
        HighlightExtraction: HighlightExtraction(highlights=[
            Highlight(author_label="autor", proposal_claim="propuesta", section_ref="Sección 1 (p. 1)", relevance="rel")
        ]),
        GapAnalysis: GapAnalysis(orphan_observations="", unmatched_clusters="", gaps_narrative="laguna importante"),
        Synthesis: Synthesis(vision_general="síntesis general", observaciones=[]),
    }


def _make_service(db_session, llm, settings=None) -> SummaryService:
    s = settings or _settings()
    return SummaryService(
        section_repo=SectionRepository(db_session),
        match_repo=MatchRepository(db_session),
        proposal_repo=ProposalRepository(db_session),
        target_repo=TargetRepository(db_session),
        llm=llm,
        settings=s,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_tracer_run_returns_markdown_and_persists(db_session, embedder):
    target = _make_target(db_session)
    section = SectionRepository(db_session).save(
        Section(
            text="texto de la sección legal relevante",
            target_id=target.id,
            is_matchable=True,
            embedding=_embed(embedder, "texto de la sección legal relevante"),
        )
    )
    proposal = ProposalRepository(db_session).save(
        Proposal(text="propuesta ciudadana", target_id=target.id)
    )
    MatchRepository(db_session).save(
        Match(
            proposal_id=proposal.id,
            section_id=section.id,
            degree="alto",
            confidence=0.9,
            explanation="vinculación directa",
            section_spans=[{"start": 0, "end": 5}],
        )
    )

    llm = FakeStructuredLLM(_full_responses())
    service = _make_service(db_session, llm)
    result = service.run(target.id)

    assert isinstance(result, str)
    assert len(result) > 0
    assert "## Principales ejes" in result

    persisted = TargetRepository(db_session).get_by_id(target.id)
    assert persisted.summary == result


def test_highlights_short_circuit_when_no_section_spans(db_session, embedder):
    """When no alto match has section_spans, highlight node must not invoke the LLM."""
    target = _make_target(db_session)
    section = SectionRepository(db_session).save(
        Section(
            text="texto sección",
            target_id=target.id,
            is_matchable=True,
            embedding=_embed(embedder, "texto sección"),
        )
    )
    proposal = ProposalRepository(db_session).save(
        Proposal(text="propuesta", target_id=target.id)
    )
    MatchRepository(db_session).save(
        Match(
            proposal_id=proposal.id,
            section_id=section.id,
            degree="alto",
            confidence=0.9,
            explanation="vinculación",
            section_spans=None,
        )
    )

    llm = FakeStructuredLLM(_full_responses())
    service = _make_service(db_session, llm)
    result = service.run(target.id)

    assert llm.calls.get(HighlightExtraction, 0) == 0
    assert "## Vinculaciones destacadas" not in result


def test_all_nodes_fail_returns_empty_and_logs_warning(db_session, embedder, caplog):
    target = _make_target(db_session)
    section = SectionRepository(db_session).save(
        Section(text="texto", target_id=target.id, embedding=_embed(embedder, "texto"))
    )
    proposal = ProposalRepository(db_session).save(
        Proposal(text="propuesta", target_id=target.id)
    )
    MatchRepository(db_session).save(
        Match(proposal_id=proposal.id, section_id=section.id, degree="alto", confidence=0.9)
    )

    failing = {schema: RuntimeError("boom") for schema in (DocumentOverview, ThemeAnalysis, HighlightExtraction, GapAnalysis, Synthesis)}
    llm = FakeStructuredLLM(failing)

    import logging
    with caplog.at_level(logging.WARNING):
        result = _make_service(db_session, llm).run(target.id)

    assert result == ""
    assert "empty" in caplog.text.lower() or "Summary generation" in caplog.text


def test_missing_target_raises_value_error(db_session):
    llm = FakeStructuredLLM({})
    service = _make_service(db_session, llm)
    with pytest.raises(ValueError, match="99999"):
        service.run(99999)


def test_persistence_happy_path(db_session, embedder):
    target = _make_target(db_session)
    section = SectionRepository(db_session).save(
        Section(
            text="texto sección para persistencia",
            target_id=target.id,
            is_matchable=True,
            embedding=_embed(embedder, "texto sección para persistencia"),
        )
    )
    proposal = ProposalRepository(db_session).save(
        Proposal(text="propuesta para persistencia", target_id=target.id)
    )
    MatchRepository(db_session).save(
        Match(
            proposal_id=proposal.id,
            section_id=section.id,
            degree="medio",
            confidence=0.7,
        )
    )

    llm = FakeStructuredLLM(_full_responses())
    service = _make_service(db_session, llm)
    markdown = service.run(target.id)

    fresh = TargetRepository(db_session).get_by_id(target.id)
    assert fresh.summary == markdown
    assert fresh.summary is not None
