"""`target_id` filters on /proposals and /matches, used by the detail page."""


def test_proposals_filtered_by_target(client, scenario):
    law = client.get("/proposals", params={"target_id": scenario.law.id}).json()
    other = client.get("/proposals", params={"target_id": scenario.other.id}).json()

    assert {p["id"] for p in law} == scenario.law_proposal_ids
    assert {p["id"] for p in other} == scenario.other_proposal_ids


def test_proposals_without_target_returns_all(client, scenario):
    proposals = client.get("/proposals").json()

    assert {p["id"] for p in proposals} == scenario.law_proposal_ids | scenario.other_proposal_ids


def test_matches_filtered_by_target(client, scenario):
    matches = client.get("/matches", params={"target_id": scenario.law.id}).json()

    assert len(matches) == 4
    assert {m["proposal_id"] for m in matches} <= scenario.law_proposal_ids


def test_matches_filtered_by_target_and_degree(client, scenario):
    matches = client.get(
        "/matches", params=[("target_id", scenario.law.id), ("degree", "alto"), ("degree", "medio")]
    ).json()

    assert sorted(m["degree"] for m in matches) == ["alto", "medio", "medio"]


def test_matches_for_empty_target_is_empty(client, scenario):
    assert client.get("/matches", params={"target_id": scenario.empty.id}).json() == []
