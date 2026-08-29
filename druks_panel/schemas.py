from datetime import datetime

from druks.schemas import BaseResponse
from druks.workflows import SubjectStatus, SubjectSummary
from pydantic import BaseModel, ConfigDict, Field

from druks_panel.contracts import AdvisorAssessment, ModeratorSynthesis
from druks_panel.types import DecisionAction


class CreateDecisionRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=3, max_length=120)
    question: str = Field(min_length=5, max_length=500)
    context: str = Field(default="", max_length=4000)


class DecisionOutcomeRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    action: DecisionAction
    note: str = Field(default="", max_length=2000)


class CreateDecisionResponse(BaseResponse):
    id: int
    run_id: str


class DecisionSummary(SubjectSummary):
    title: str
    question: str
    recommendation: DecisionAction | None
    outcome: DecisionAction | None
    created_at: datetime


class DecisionDetail(DecisionSummary):
    model_config = ConfigDict(from_attributes=True)

    context: str
    assessments: list[AdvisorAssessment]
    synthesis: ModeratorSynthesis | None
    outcome_note: str
    decided_at: datetime | None
    status: SubjectStatus
