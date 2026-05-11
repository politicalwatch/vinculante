import pytest

from vinculante.application.embedding.embedder_service import ProposalEmbedderService
from vinculante.domain.entities import Proposal, TargetDocument
from vinculante.infrastructure.db.repositories.proposals import ProposalRepository
from vinculante.infrastructure.db.repositories.targets import TargetRepository


def _make_target(db_session, title: str = "t") -> TargetDocument:
    return TargetRepository(db_session).save(TargetDocument(title=title, author="a"))


def test_embeds_all_unembedded_proposals(db_session, embedder):
    repo = ProposalRepository(db_session)
    repo.bulk_save([
        Proposal(text="uno", source_file="a.csv"),
        Proposal(text="dos", source_file="a.csv"),
        Proposal(text="tres", source_file="a.csv"),
    ])

    service = ProposalEmbedderService(proposal_repo=repo, embedder=embedder)
    count = service.embed_proposals()

    assert count == 3
    assert all(p.embedding is not None for p in repo.get_all())


def test_skips_already_embedded_proposals(db_session, embedder):
    repo = ProposalRepository(db_session)
    repo.bulk_save([
        Proposal(text="uno", source_file="a.csv"),
        Proposal(text="dos", source_file="a.csv"),
    ])
    service = ProposalEmbedderService(proposal_repo=repo, embedder=embedder)
    service.embed_proposals()

    recount = service.embed_proposals()

    assert recount == 0


def test_source_file_filter_embeds_only_matching_proposals(db_session, embedder):
    repo = ProposalRepository(db_session)
    repo.bulk_save([
        Proposal(text="a1", source_file="a.csv"),
        Proposal(text="a2", source_file="a.csv"),
        Proposal(text="b1", source_file="b.csv"),
    ])
    service = ProposalEmbedderService(proposal_repo=repo, embedder=embedder)

    count = service.embed_proposals(source_file="a.csv")

    assert count == 2
    all_proposals = repo.get_all()
    assert all(p.embedding is not None for p in all_proposals if p.source_file == "a.csv")
    assert all(p.embedding is None for p in all_proposals if p.source_file == "b.csv")


def test_target_id_filter_embeds_only_that_targets_proposals(db_session, embedder):
    t1 = _make_target(db_session, title="t1")
    t2 = _make_target(db_session, title="t2")
    repo = ProposalRepository(db_session)
    repo.bulk_save([
        Proposal(text="a1", source_file="a.csv", target_id=t1.id),
        Proposal(text="a2", source_file="a.csv", target_id=t1.id),
        Proposal(text="b1", source_file="b.csv", target_id=t2.id),
    ])
    service = ProposalEmbedderService(proposal_repo=repo, embedder=embedder)

    count = service.embed_proposals(target_id=t1.id)

    assert count == 2
    all_proposals = repo.get_all()
    assert all(p.embedding is not None for p in all_proposals if p.target_id == t1.id)
    assert all(p.embedding is None for p in all_proposals if p.target_id == t2.id)


def test_raises_when_both_source_file_and_target_id_given(db_session, embedder):
    repo = ProposalRepository(db_session)
    service = ProposalEmbedderService(proposal_repo=repo, embedder=embedder)

    with pytest.raises(ValueError, match="mutually exclusive"):
        service.embed_proposals(source_file="a.csv", target_id=1)


def test_embeds_across_multiple_batches(db_session, embedder):
    repo = ProposalRepository(db_session)
    repo.bulk_save([Proposal(text=f"p{i}", source_file="a.csv") for i in range(5)])
    service = ProposalEmbedderService(proposal_repo=repo, embedder=embedder, batch_size=2)

    count = service.embed_proposals()

    assert count == 5
    assert all(p.embedding is not None for p in repo.get_all())
