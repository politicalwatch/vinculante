from langchain_core.language_models.fake_chat_models import FakeListChatModel

from vinculante.application.clear_language.generator_service import ClearLanguageGeneratorService
from vinculante.domain.entities import Section, TargetDocument
from vinculante.infrastructure.db.repositories.sections import SectionRepository
from vinculante.infrastructure.db.repositories.targets import TargetRepository


def _make_target(db_session, title: str = "t") -> TargetDocument:
    return TargetRepository(db_session).save(TargetDocument(title=title, author="a"))


def test_generates_clear_language_for_section(db_session):
    target = _make_target(db_session)
    repo = SectionRepository(db_session)
    original_text = "Artículo 1. Objeto de la presente norma."
    llm_output = "  El artículo 1 explica el propósito de esta ley.  "
    section = repo.save(Section(text=original_text, clear_language=original_text, target_id=target.id))

    llm = FakeListChatModel(responses=[llm_output])
    service = ClearLanguageGeneratorService(section_repo=repo, llm=llm)
    count = service.generate()

    assert count == 1
    refreshed = repo.get_by_id(section.id)
    assert refreshed.clear_language == llm_output.strip()
    assert refreshed.clear_language != original_text


def test_skips_sections_already_generated(db_session):
    target = _make_target(db_session)
    repo = SectionRepository(db_session)
    repo.save(Section(text="original legal text", clear_language="simplified text", target_id=target.id))

    llm = FakeListChatModel(responses=["should not be called"])
    service = ClearLanguageGeneratorService(section_repo=repo, llm=llm)
    count = service.generate()

    assert count == 0
    refreshed = repo.get_all()[0]
    assert refreshed.clear_language == "simplified text"


def test_force_regenerates_all_sections(db_session):
    target = _make_target(db_session)
    repo = SectionRepository(db_session)
    repo.bulk_save([
        Section(text="s1 original", clear_language="s1 simplified", target_id=target.id),
        Section(text="s2 original", clear_language="s2 simplified", target_id=target.id),
    ])

    llm = FakeListChatModel(responses=["regenerated"])
    count = ClearLanguageGeneratorService(section_repo=repo, llm=llm).generate(force=True)

    assert count == 2
    assert all(s.clear_language == "regenerated" for s in repo.get_all())


def test_clears_embedding_when_clear_language_changes(db_session):
    target = _make_target(db_session)
    repo = SectionRepository(db_session)
    section = repo.save(
        Section(
            text="original",
            clear_language="original",
            target_id=target.id,
            embedding=[0.1] * 8,
        )
    )

    llm = FakeListChatModel(responses=["rewritten"])
    ClearLanguageGeneratorService(section_repo=repo, llm=llm).generate()

    refreshed = repo.get_by_id(section.id)
    assert refreshed.clear_language == "rewritten"
    assert refreshed.embedding is None


def test_skips_non_matchable_sections(db_session):
    target = _make_target(db_session)
    repo = SectionRepository(db_session)
    heading = repo.save(Section(text="Cap I", clear_language="Cap I", is_matchable=False, target_id=target.id))

    llm = FakeListChatModel(responses=["should not be called"])
    count = ClearLanguageGeneratorService(section_repo=repo, llm=llm).generate(target_id=target.id)

    assert count == 0
    assert repo.get_by_id(heading.id).clear_language == "Cap I"


def test_target_id_filter_leaves_other_targets_untouched(db_session):
    t1 = _make_target(db_session, title="t1")
    t2 = _make_target(db_session, title="t2")
    repo = SectionRepository(db_session)
    repo.bulk_save([
        Section(text="a", clear_language="a", target_id=t1.id),
        Section(text="b", clear_language="b", target_id=t2.id),
    ])

    llm = FakeListChatModel(responses=["rewritten"])
    count = ClearLanguageGeneratorService(section_repo=repo, llm=llm).generate(target_id=t1.id)

    assert count == 1
    by_target = {s.target_id: s for s in repo.get_all()}
    assert by_target[t1.id].clear_language == "rewritten"
    assert by_target[t2.id].clear_language == "b"
