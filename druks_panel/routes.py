from fastapi import APIRouter, status

from druks_panel.models import Decision
from druks_panel.schemas import CreateDecisionRequest, CreateDecisionResponse, DecisionSummary
from druks_panel.workflows import Deliberate

# Every APIRouter declared here mounts under /api/panel.
router = APIRouter(prefix="/decisions")


@router.get("", response_model=list[DecisionSummary], response_model_by_alias=True)
async def list_decisions() -> list[Decision]:
    return await Decision.all()


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
