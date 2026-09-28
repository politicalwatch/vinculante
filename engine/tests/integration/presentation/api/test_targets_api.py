def _by_id(targets: list[dict]) -> dict[int, dict]:
    return {target["id"]: target for target in targets}


def test_list_targets_returns_signature_counts(client, scenario):
    response = client.get("/targets")

    assert response.status_code == 200
    targets = _by_id(response.json())
    assert targets[scenario.law.id] == {
        "id": scenario.law.id,
        "title": "Ley de prueba",
        "author": "Gobierno",
        "date": None,
        "version": None,
        "topic": "digitales",
        "articles": 3,
        "touched": 2,
        "proposals": 3,
        "incorporated": 2,
    }
    assert targets[scenario.other.id]["articles"] == 1
    assert targets[scenario.other.id]["touched"] == 1
    assert targets[scenario.other.id]["proposals"] == 1
    assert targets[scenario.other.id]["incorporated"] == 1


def test_list_targets_counts_zero_for_empty_target(client, scenario):
    targets = _by_id(client.get("/targets").json())

    empty = targets[scenario.empty.id]
    assert empty["topic"] is None
    counts = (empty["articles"], empty["touched"], empty["proposals"], empty["incorporated"])
    assert counts == (0, 0, 0, 0)


def test_list_targets_newest_first(client, scenario):
    ids = [target["id"] for target in client.get("/targets").json()]

    assert ids == sorted(ids, reverse=True)


def test_get_target_includes_topic_and_stats(client, scenario):
    response = client.get(f"/targets/{scenario.law.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["topic"] == "digitales"
    assert body["stats"] is not None


def test_get_unknown_target_is_404(client, scenario):
    assert client.get("/targets/999999").status_code == 404
