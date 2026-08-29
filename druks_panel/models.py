from datetime import datetime
from typing import Any

from druks.db import StoredSubject, db_session
from sqlalchemy import Text, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from druks_panel.contracts import AdvisorAssessment, ModeratorSynthesis
from druks_panel.schemas import DecisionDetail, DecisionSummary
from druks_panel.types import DecisionAction


class Decision(StoredSubject):
    __tablename__ = "panel_decisions"

    title: Mapped[str]
    question: Mapped[str] = mapped_column(Text)
    context: Mapped[str] = mapped_column(Text, default="")
    assessments: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    synthesis: Mapped[dict[str, Any] | None] = mapped_column(JSONB, default=None)
    recommendation: Mapped[str | None]
    outcome: Mapped[str | None]
    outcome_note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(default=StoredSubject.utc_now)
    decided_at: Mapped[datetime | None]

    @classmethod
    async def create(cls, *, title: str, question: str, context: str = "") -> "Decision":
        decision = cls(title=title, question=question, context=context)
        db_session().add(decision)
        await db_session().flush()
        return decision

    @classmethod
    async def get(cls, decision_id: int) -> "Decision | None":
        return await db_session().get(cls, decision_id)

    @classmethod
    async def list_recent(cls, *, limit: int = 100) -> list["Decision"]:
        stmt = select(cls).order_by(cls.created_at.desc(), cls.id.desc()).limit(limit)
        return list(await db_session().scalars(stmt))

    def get_label(self) -> str:
        return self.title

    def get_summary(self) -> DecisionSummary:
        return DecisionSummary.model_validate(self)

    @classmethod
    async def list_summaries(cls, account_id: str | None) -> list[DecisionSummary]:
        return [decision.get_summary() for decision in await cls.list_recent()]

    async def save_panel(
        self,
        *,
        assessments: list[dict[str, Any]],
        synthesis: dict[str, Any],
        recommendation: DecisionAction,
    ) -> None:
        self.assessments = assessments
        self.synthesis = synthesis
        self.recommendation = recommendation
        await db_session().flush()

    async def save_outcome(self, *, action: DecisionAction, note: str) -> None:
        self.outcome = action
        self.outcome_note = note
        self.decided_at = self.utc_now()
        await db_session().flush()

    async def get_detail(self) -> DecisionDetail:
        from druks_panel.workflows import Deliberate

        return DecisionDetail(
            **self.get_summary().model_dump(),
            context=self.context,
            assessments=[AdvisorAssessment.model_validate(item) for item in self.assessments],
            synthesis=ModeratorSynthesis.model_validate(self.synthesis) if self.synthesis else None,
            outcome_note=self.outcome_note,
            decided_at=self.decided_at,
            status=await self.get_status(workflow=Deliberate),
        )
