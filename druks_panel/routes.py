from druks.workflows import WorkflowError
from fastapi import APIRouter, HTTPException, status

from druks_panel.models import Decision
from druks_panel.schemas import (
    CreateDecisionRequest,
    CreateDecisionResponse,
    DecisionDetail,
    DecisionOutcomeRequest,
)
from druks_panel.workflows import Deliberate, RecordDecision

router = APIRouter(prefix="/decisions", tags=["decisions"])


async def _get_decision(decision_id: int) -> Decision:
    decision = await Decision.get(decision_id)
    if not decision:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision not found")
    return decision


@router.get("", response_model=list[DecisionDetail], response_model_by_alias=True)
async def list_decisions() -> list[DecisionDetail]:
    return [await decision.get_detail() for decision in await Decision.list_recent()]


@router.post(
    "",
    response_model=CreateDecisionResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
async def create_decision(body: CreateDecisionRequest) -> CreateDecisionResponse:
    decision = await Decision.create(
        title=body.title.strip(),
        question=body.question.strip(),
        context=body.context.strip(),
    )
    run_id = await Deliberate.start(subject=decision)
    return CreateDecisionResponse(id=decision.id, run_id=run_id)


@router.get("/{decision_id}", response_model=DecisionDetail, response_model_by_alias=True)
async def get_decision(decision_id: int) -> DecisionDetail:
    return await (await _get_decision(decision_id)).get_detail()


@router.post("/{decision_id}/outcome", status_code=status.HTTP_202_ACCEPTED)
async def record_outcome(decision_id: int, body: DecisionOutcomeRequest) -> dict[str, str]:
    decision = await _get_decision(decision_id)
    try:
        await RecordDecision.answer(decision, action=body.action, note=body.note.strip())
    except WorkflowError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    return {"status": "accepted"}
