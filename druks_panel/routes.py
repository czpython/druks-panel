from druks.workflows import WorkflowError
from fastapi import APIRouter, HTTPException, status

from druks_panel.models import Decision
from druks_panel.schemas import (
    CreateDecisionRequest,
    CreateDecisionResponse,
    DecisionOutcomeRequest,
    DecisionSummary,
)
from druks_panel.workflows import Deliberate, RecordDecision

# Every APIRouter declared here mounts under /api/panel.
router = APIRouter(prefix="/decisions")


@router.get("", response_model=list[DecisionSummary], response_model_by_alias=True)
async def list_decisions() -> list[DecisionSummary]:
    return [decision.get_summary() for decision in await Decision.list_recent()]


@router.post(
    "",
    response_model=CreateDecisionResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    operation_id="create_decision",
)
async def create_decision(body: CreateDecisionRequest) -> CreateDecisionResponse:
    decision = await Decision.create(
        title=body.title,
        question=body.question,
        context=body.context,
    )
    run_id = await Deliberate.start(subject=decision)
    return CreateDecisionResponse(id=decision.id, run_id=run_id)


@router.post(
    "/{decision_id}/outcome",
    status_code=status.HTTP_202_ACCEPTED,
    operation_id="record_outcome",
)
async def record_outcome(decision_id: int, body: DecisionOutcomeRequest) -> dict[str, str]:
    decision = await Decision.get(decision_id)
    if not decision:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No decision {decision_id}.")
    try:
        await RecordDecision.answer(decision, action=body.action, note=body.note)
    except WorkflowError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    return {"result": "recorded"}
