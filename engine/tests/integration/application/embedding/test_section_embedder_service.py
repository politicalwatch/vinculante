from vinculante.application.embedding.embedder_service import SectionEmbedderService
from vinculante.domain.entities import Section, TargetDocument
from vinculante.infrastructure.db.repositories.sections import SectionRepository
from vinculante.infrastructure.db.repositories.targets import TargetRepository


def _make_target(db_session, title: str = "t") -> TargetDocument:
    return TargetRepository(db_session).save(TargetDocument(title=title, author="a"))


def test_embeds_all_unembedded_sections(db_session, embedder):
    target = _make_target(db_session)
    repo = SectionRepository(db_session)
    repo.bulk_save([
        Section(text="s1", plain_text="s1", target_id=target.id),
        Section(text="s2", plain_text="s2", target_id=target.id),
    ])

    service = SectionEmbedderService(section_repo=repo, embedder=embedder)
    count = service.embed_sections()

    assert count == 2
    assert all(s.embedding is not None for s in repo.get_all())


def test_target_id_filter_embeds_only_that_targets_sections(db_session, embedder):
    t1 = _make_target(db_session, title="t1")
    t2 = _make_target(db_session, title="t2")
    repo = SectionRepository(db_session)
    repo.bulk_save([
        Section(text="a", plain_text="a", target_id=t1.id),
        Section(text="b", plain_text="b", target_id=t1.id),
        Section(text="c", plain_text="c", target_id=t2.id),
    ])

    count = SectionEmbedderService(section_repo=repo, embedder=embedder).embed_sections(target_id=t1.id)

    assert count == 2
    all_sections = repo.get_all()
    assert all(s.embedding is not None for s in all_sections if s.target_id == t1.id)
    assert all(s.embedding is None for s in all_sections if s.target_id == t2.id)


def test_uses_plain_text_when_set_otherwise_falls_back_to_text(db_session, embedder):
    target = _make_target(db_session)
    repo = SectionRepository(db_session)
    with_plain = Section(text="dirty", plain_text="clean", target_id=target.id)
    without_plain = Section(text="raw", plain_text=None, target_id=target.id)
    repo.bulk_save([with_plain, without_plain])

    SectionEmbedderService(section_repo=repo, embedder=embedder).embed_sections()

    refreshed = {s.id: s for s in repo.get_all()}
    assert list(refreshed[with_plain.id].embedding) == list(embedder.embed_query("clean"))
    assert list(refreshed[without_plain.id].embedding) == list(embedder.embed_query("raw"))
