import json
from collections.abc import Awaitable
from typing import cast

from druks.workflows import Gate, Workflow, step

from druks_panel.app import Panel
from druks_panel.models import Decision
from druks_panel.types import DecisionAction


class RecordDecision(Gate):
    name = "record_decision"
    action: DecisionAction
    note: str = ""


class Deliberate(Workflow):
    subject = Decision

    async def run_multistep(self) -> dict[str, str]:
        decision = await self._get_decision()
        context = decision.context or "No additional context was provided."

        opportunity = await Panel.opportunity(
            title=decision.title,
            question=decision.question,
            context=context,
        )
        risk = await Panel.risk(
            title=decision.title,
            question=decision.question,
            context=context,
        )
        execution = await Panel.execution(
            title=decision.title,
            question=decision.question,
            context=context,
        )
        assessments = [
            opportunity.model_dump(mode="json"),
            risk.model_dump(mode="json"),
            execution.model_dump(mode="json"),
        ]
        synthesis = await Panel.moderator(
            title=decision.title,
            question=decision.question,
            context=context,
            assessments_json=json.dumps(assessments, indent=2),
        )
        await self.persist_panel(
            assessments=assessments,
            synthesis=synthesis.model_dump(mode="json"),
            recommendation=synthesis.recommendation,
        )

        reply = await RecordDecision.wait(
            input_request={
                "presentation": "external",
                "label": "Record the decision",
                "url": f"/panel/decisions/{decision.id}",
            }
        )
        await self.persist_outcome(action=reply.action, note=reply.note)
        return {"action": reply.action}

    @step
    async def persist_panel(
        self,
        *,
        assessments: list[dict[str, object]],
        synthesis: dict[str, object],
        recommendation: DecisionAction,
    ) -> None:
        decision = await self._get_decision()
        await decision.save_panel(
            assessments=assessments,
            synthesis=synthesis,
            recommendation=recommendation,
        )

    @step
    async def persist_outcome(self, *, action: DecisionAction, note: str) -> None:
        decision = await self._get_decision()
        await decision.save_outcome(action=action, note=note)

    async def _get_decision(self) -> Decision:
        return await cast(Awaitable[Decision], self.subject)
