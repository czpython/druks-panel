from unittest import mock

from druks_panel.models import Decision
from druks_panel.workflows import Deliberate, RecordDecision


async def test_decision_routes_create_list_and_answer(druks_client, monkeypatch):
    start = mock.AsyncMock(return_value="run-1")
    answer = mock.AsyncMock()
    monkeypatch.setattr(Deliberate, "start", staticmethod(start))
    monkeypatch.setattr(RecordDecision, "answer", staticmethod(answer))

    created = await druks_client.post(
        "/api/panel/decisions",
        json={
            "title": "Launch the pilot",
            "question": "Should we launch the pilot in September?",
            "context": "The team has two weeks of capacity.",
        },
    )

    assert created.status_code == 201
    assert created.json()["runId"] == "run-1"
    decision = await Decision.get(created.json()["id"])
    assert start.await_count == 1
    assert start.await_args.kwargs["subject"].id == decision.id

    listed = await druks_client.get("/api/panel/decisions")

    assert listed.status_code == 200
    assert listed.json()[0]["title"] == "Launch the pilot"
    assert listed.json()[0]["status"]["state"] == "scheduled"

    response = await druks_client.post(
        f"/api/panel/decisions/{decision.id}/outcome",
        json={"action": "proceed", "note": "Start with five teams."},
    )

    assert response.status_code == 202
    assert answer.await_count == 1
    assert answer.await_args.args[0].id == decision.id
    assert answer.await_args.kwargs == {
        "action": "proceed",
        "note": "Start with five teams.",
    }
