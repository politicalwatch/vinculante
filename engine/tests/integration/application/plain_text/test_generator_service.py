from langchain_core.language_models.fake_chat_models import FakeListChatModel

from vinculante.application.plain_text.generator_service import PlainTextGeneratorService
from vinculante.domain.entities import Section, TargetDocument
from vinculante.infrastructure.db.repositories.sections import SectionRepository
from vinculante.infrastructure.db.repositories.targets import TargetRepository


def _make_target(db_session, title: str = "t") -> TargetDocument:
    return TargetRepository(db_session).save(TargetDocument(title=title, author="a"))


def test_generates_plain_text_for_section(db_session):
    target = _make_target(db_session)
    repo = SectionRepository(db_session)
    original_text = "Artículo 1. Objeto de la presente norma."
    llm_output = "  El artículo 1 explica el propósito de esta ley.  "
    section = repo.save(Section(text=original_text, plain_text=original_text, target_id=target.id))

    llm = FakeListChatModel(responses=[llm_output])
    service = PlainTextGeneratorService(section_repo=repo, llm=llm)
    count = service.generate()

    assert count == 1
    refreshed = repo.get_by_id(section.id)
    assert refreshed.plain_text == llm_output.strip()
    assert refreshed.plain_text != original_text


def test_skips_sections_already_generated(db_session):
    target = _make_target(db_session)
    repo = SectionRepository(db_session)
    repo.save(Section(text="original legal text", plain_text="simplified text", target_id=target.id))

    llm = FakeListChatModel(responses=["should not be called"])
    service = PlainTextGeneratorService(section_repo=repo, llm=llm)
    count = service.generate()

    assert count == 0
    refreshed = repo.get_all()[0]
    assert refreshed.plain_text == "simplified text"


def test_force_regenerates_all_sections(db_session):
    target = _make_target(db_session)
    repo = SectionRepository(db_session)
    repo.bulk_save([
        Section(text="s1 original", plain_text="s1 simplified", target_id=target.id),
        Section(text="s2 original", plain_text="s2 simplified", target_id=target.id),
    ])

    llm = FakeListChatModel(responses=["regenerated"])
    count = PlainTextGeneratorService(section_repo=repo, llm=llm).generate(force=True)

    assert count == 2
    assert all(s.plain_text == "regenerated" for s in repo.get_all())


def test_clears_embedding_when_plain_text_changes(db_session):
    target = _make_target(db_session)
    repo = SectionRepository(db_session)
    section = repo.save(
        Section(
            text="original",
            plain_text="original",
            target_id=target.id,
            embedding=[0.1] * 8,
        )
    )

    llm = FakeListChatModel(responses=["rewritten"])
    PlainTextGeneratorService(section_repo=repo, llm=llm).generate()

    refreshed = repo.get_by_id(section.id)
    assert refreshed.plain_text == "rewritten"
    assert refreshed.embedding is None


def test_target_id_filter_leaves_other_targets_untouched(db_session):
    t1 = _make_target(db_session, title="t1")
    t2 = _make_target(db_session, title="t2")
    repo = SectionRepository(db_session)
    repo.bulk_save([
        Section(text="a", plain_text="a", target_id=t1.id),
        Section(text="b", plain_text="b", target_id=t2.id),
    ])

    llm = FakeListChatModel(responses=["rewritten"])
    count = PlainTextGeneratorService(section_repo=repo, llm=llm).generate(target_id=t1.id)

    assert count == 1
    by_target = {s.target_id: s for s in repo.get_all()}
    assert by_target[t1.id].plain_text == "rewritten"
    assert by_target[t2.id].plain_text == "b"
