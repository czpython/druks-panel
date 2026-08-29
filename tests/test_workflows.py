import json
from unittest import mock

from druks_panel.app import Panel
from druks_panel.contracts import AdvisorAssessment, ModeratorSynthesis
from druks_panel.models import Decision
from druks_panel.workflows import Deliberate, RecordDecision


def assessment(perspective):
    return AdvisorAssessment(
        perspective=perspective,
        position="yes_with_conditions",
        headline=f"{perspective.title()} view",
        rationale=["Evidence supports a bounded test."],
        uncertainties=["Demand is still uncertain."],
        confidence=70,
    )


async def test_deliberate_collects_independent_views_then_parks(druks_db, monkeypatch):
    decision = await Decision.create(
        title="Launch the pilot",
        question="Should we launch the pilot in September?",
        context="Two weeks of capacity are available.",
    )
    opportunity = mock.AsyncMock(return_value=assessment("opportunity"))
    risk = mock.AsyncMock(return_value=assessment("risk"))
    execution = mock.AsyncMock(return_value=assessment("execution"))
    synthesis = ModeratorSynthesis(
        recommendation="proceed",
        summary="A bounded pilot is justified.",
        common_ground=["Keep the first cohort small."],
        tradeoffs=["Speed versus completeness."],
        questions_to_resolve=["What ends the pilot?"],
        next_step="Choose five teams.",
    )
    moderator = mock.AsyncMock(return_value=synthesis)
    wait = mock.AsyncMock(return_value=RecordDecision(action="proceed", note="Keep it small."))
    persist_panel = mock.AsyncMock()
    persist_outcome = mock.AsyncMock()
    monkeypatch.setattr(Panel, "opportunity", staticmethod(opportunity))
    monkeypatch.setattr(Panel, "risk", staticmethod(risk))
    monkeypatch.setattr(Panel, "execution", staticmethod(execution))
    monkeypatch.setattr(Panel, "moderator", staticmethod(moderator))
    monkeypatch.setattr(RecordDecision, "wait", staticmethod(wait))

    workflow = Deliberate()
    workflow.subject = decision
    workflow.persist_panel = persist_panel
    workflow.persist_outcome = persist_outcome

    result = await workflow.run_multistep()

    assert result == {"action": "proceed"}
    for advisor in (opportunity, risk, execution):
        advisor.assert_awaited_once_with(
            title=decision.title,
            question=decision.question,
            context=decision.context,
        )
    moderator.assert_awaited_once()
    assert [
        item["perspective"] for item in json.loads(moderator.await_args.kwargs["assessments_json"])
    ] == [
        "opportunity",
        "risk",
        "execution",
    ]
    persist_panel.assert_awaited_once()
    wait.assert_awaited_once_with(
        input_request={
            "presentation": "external",
            "label": "Record the decision",
            "url": f"/panel/decisions/{decision.id}",
        }
    )
    persist_outcome.assert_awaited_once_with(action="proceed", note="Keep it small.")
