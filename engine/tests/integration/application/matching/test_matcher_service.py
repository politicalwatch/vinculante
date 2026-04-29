import pytest
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.runnables import RunnableLambda

from vinculante.application.matching.matcher_service import MatcherService
from vinculante.application.matching.schemas import MatchScore
from vinculante.domain.entities import Match, MatchStatus, Proposal, Section, TargetDocument
from vinculante.infrastructure.config.settings import Settings
from vinculante.infrastructure.db.repositories.matches import MatchRepository
from vinculante.infrastructure.db.repositories.proposals import ProposalRepository
from vinculante.infrastructure.db.repositories.sections import SectionRepository
from vinculante.infrastructure.db.repositories.targets import TargetRepository


class FakeStructuredLLM:
    """Minimal chat-model stand-in that supports `with_structured_output`.

    Cycles through `responses` like `FakeListChatModel` does.
    """

    def __init__(self, responses: list[MatchScore]) -> None:
        self._responses = list(responses)
        self._i = 0

    def with_structured_output(self, schema, **kwargs):
        fake = self

        async def _scorer(_input):
            r = fake._responses[fake._i % len(fake._responses)]
            fake._i += 1
            return r

        return RunnableLambda(_scorer)


def _settings(**overrides) -> Settings:
    base = dict(
        db_url="postgresql+psycopg2://x:x@localhost/x",
        cache_redis_host="redis://localhost",
        matching_top_k_pct=0.10,
        matching_top_k_min=5,
        matching_top_k_max=20,
        matching_confidence_threshold=0.5,
        matching_concurrency=2,
        matching_strategy="one-to-one",
        matching_prompt_version="v5",
    )
    return Settings(**{**base, **overrides})


def _make_target(db_session, title: str = "t") -> TargetDocument:
    return TargetRepository(db_session).save(TargetDocument(title=title, author="a"))


def _embed(embedder: DeterministicFakeEmbedding, text: str) -> list[float]:
    return embedder.embed_query(text)


def _score(degree: str, explanation: str, confidence: float, evidence_quotes: list[str] | None = None) -> MatchScore:
    return MatchScore(degree=degree, explanation=explanation, confidence=confidence, evidence_quotes=evidence_quotes or [])


def test_tracer_saves_match_with_llm_fields(db_session, embedder):
    target = _make_target(db_session)
    section_repo = SectionRepository(db_session)
    proposal_repo = ProposalRepository(db_session)
    match_repo = MatchRepository(db_session)

    section = section_repo.save(
        Section(text="fragmento legal relevante de prueba", clear_language="fragmento legal relevante de prueba", target_id=target.id,
                embedding=_embed(embedder, "fragmento legal relevante de prueba"))
    )
    proposal = proposal_repo.save(
        Proposal(text="propuesta ciudadana", target_id=target.id,
                 embedding=_embed(embedder, "propuesta ciudadana"))
    )

    llm = FakeStructuredLLM(responses=[_score("alto", "cubre directamente", 0.9, evidence_quotes=["fragmento legal relevante"])])
    service = MatcherService(
        proposal_repo=proposal_repo,
        section_repo=section_repo,
        match_repo=match_repo,
        embedder=embedder,
        llm=llm,
        settings=_settings(),
    )
    matches = service.run(target_id=target.id)

    assert len(matches) == 1
    m = matches[0]
    assert m.proposal_id == proposal.id
    assert m.section_id == section.id
    assert m.degree == "alto"
    assert m.explanation == "cubre directamente"
    assert m.confidence == pytest.approx(0.9)
    assert m.status == MatchStatus.pending


def test_below_threshold_is_persisted(db_session, embedder):
    """Low-confidence matches are stored so the threshold can be tuned post-hoc."""
    target = _make_target(db_session)
    section_repo = SectionRepository(db_session)
    proposal_repo = ProposalRepository(db_session)
    match_repo = MatchRepository(db_session)

    section_repo.save(
        Section(text="texto del fragmento legal", clear_language="texto del fragmento legal", target_id=target.id,
                embedding=_embed(embedder, "texto del fragmento legal"))
    )
    proposal_repo.save(
        Proposal(text="propuesta", target_id=target.id,
                 embedding=_embed(embedder, "propuesta"))
    )

    llm = FakeStructuredLLM(responses=[_score("bajo", "relación débil", 0.3, evidence_quotes=["texto del fragmento"])])
    service = MatcherService(
        proposal_repo=proposal_repo,
        section_repo=section_repo,
        match_repo=match_repo,
        embedder=embedder, llm=llm,
        settings=_settings(matching_confidence_threshold=0.5),
    )
    matches = service.run(target_id=target.id)

    assert len(matches) == 1
    assert matches[0].degree == "bajo"
    assert matches[0].confidence == pytest.approx(0.3)
    # Accepted-only accessor applies the threshold and excludes it.
    assert match_repo.get_accepted_by_target(target.id, min_confidence=0.5) == []


def test_degree_ninguno_is_persisted(db_session, embedder):
    """Ninguno matches are stored for debugging but excluded by accepted-only accessor."""
    target = _make_target(db_session)
    section_repo = SectionRepository(db_session)
    proposal_repo = ProposalRepository(db_session)
    match_repo = MatchRepository(db_session)

    section_repo.save(
        Section(text="s", clear_language="texto", target_id=target.id,
                embedding=_embed(embedder, "texto"))
    )
    proposal_repo.save(
        Proposal(text="propuesta", target_id=target.id,
                 embedding=_embed(embedder, "propuesta"))
    )

    llm = FakeStructuredLLM(responses=[_score("ninguno", "sin relación", 0.95)])
    service = MatcherService(
        proposal_repo=proposal_repo,
        section_repo=section_repo,
        match_repo=match_repo,
        embedder=embedder, llm=llm,
        settings=_settings(),
    )
    matches = service.run(target_id=target.id)

    assert len(matches) == 1
    assert matches[0].degree == "ninguno"
    assert matches[0].explanation == "sin relación"
    assert match_repo.get_accepted_by_target(target.id) == []


def test_multiple_candidates_all_saved(db_session, embedder):
    target = _make_target(db_session)
    section_repo = SectionRepository(db_session)
    proposal_repo = ProposalRepository(db_session)
    match_repo = MatchRepository(db_session)

    for i in range(3):
        section_repo.save(
            Section(text=f"texto del fragmento {i}", clear_language=f"texto del fragmento {i}", target_id=target.id,
                    embedding=_embed(embedder, f"texto del fragmento {i}"))
        )
    proposal_repo.save(
        Proposal(text="propuesta", target_id=target.id,
                 embedding=_embed(embedder, "propuesta"))
    )

    llm = FakeStructuredLLM(responses=[_score("medio", "relación parcial", 0.7, evidence_quotes=["texto del fragmento"])])
    service = MatcherService(
        proposal_repo=proposal_repo,
        section_repo=section_repo,
        match_repo=match_repo,
        embedder=embedder, llm=llm,
        settings=_settings(matching_top_k_min=3, matching_top_k_max=3),
    )
    matches = service.run(target_id=target.id)

    assert len(matches) == 3
    assert all(m.degree == "medio" for m in matches)


def test_sections_scoped_to_target(db_session, embedder):
    t1 = _make_target(db_session, "t1")
    t2 = _make_target(db_session, "t2")
    section_repo = SectionRepository(db_session)
    proposal_repo = ProposalRepository(db_session)
    match_repo = MatchRepository(db_session)

    section_repo.save(
        Section(text="s1", clear_language="s1", target_id=t1.id,
                embedding=_embed(embedder, "s1"))
    )
    section_repo.save(
        Section(text="s2", clear_language="s2", target_id=t2.id,
                embedding=_embed(embedder, "s2"))
    )
    proposal_repo.save(
        Proposal(text="p", target_id=t1.id, embedding=_embed(embedder, "p"))
    )

    llm = FakeStructuredLLM(responses=[_score("alto", "directo", 0.9)])
    service = MatcherService(
        proposal_repo=proposal_repo,
        section_repo=section_repo,
        match_repo=match_repo,
        embedder=embedder, llm=llm,
        settings=_settings(),
    )
    matches = service.run(target_id=t1.id)

    section_ids = {m.section_id for m in matches}
    t1_ids = {s.id for s in section_repo.get_by_target(t1.id)}
    assert section_ids <= t1_ids


def test_proposals_scoped_to_target(db_session, embedder):
    t1 = _make_target(db_session, "t1")
    t2 = _make_target(db_session, "t2")
    section_repo = SectionRepository(db_session)
    proposal_repo = ProposalRepository(db_session)
    match_repo = MatchRepository(db_session)

    section_repo.save(
        Section(text="s", clear_language="s", target_id=t1.id,
                embedding=_embed(embedder, "s"))
    )
    proposal_repo.save(Proposal(text="p1", target_id=t1.id, embedding=_embed(embedder, "p1")))
    proposal_repo.save(Proposal(text="p2", target_id=t2.id, embedding=_embed(embedder, "p2")))

    llm = FakeStructuredLLM(responses=[_score("alto", "directo", 0.9)])
    service = MatcherService(
        proposal_repo=proposal_repo,
        section_repo=section_repo,
        match_repo=match_repo,
        embedder=embedder, llm=llm,
        settings=_settings(),
    )
    matches = service.run(target_id=t1.id)

    proposal_ids = {m.proposal_id for m in matches}
    t1_proposal_ids = {p.id for p in proposal_repo.get_by_target(t1.id)}
    assert proposal_ids <= t1_proposal_ids


def test_skip_matched_skips_proposals_with_existing_matches(db_session, embedder):
    target = _make_target(db_session)
    section_repo = SectionRepository(db_session)
    proposal_repo = ProposalRepository(db_session)
    match_repo = MatchRepository(db_session)

    section = section_repo.save(
        Section(text="s", clear_language="s", target_id=target.id,
                embedding=_embed(embedder, "s"))
    )
    proposal = proposal_repo.save(
        Proposal(text="p", target_id=target.id, embedding=_embed(embedder, "p"))
    )
    match_repo.save(Match(proposal_id=proposal.id, section_id=section.id,
                          degree="alto", confidence=0.9, explanation="ya existe"))

    llm = FakeStructuredLLM(responses=[_score("alto", "no debería llamarse", 0.9)])
    service = MatcherService(
        proposal_repo=proposal_repo,
        section_repo=section_repo,
        match_repo=match_repo,
        embedder=embedder, llm=llm,
        settings=_settings(),
    )
    new_matches = service.run(target_id=target.id, skip_matched=True)

    assert new_matches == []
    assert len(match_repo.get_all()) == 1
