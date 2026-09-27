from datetime import datetime
from typing import Any

from druks.db import StoredSubject
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from druks_panel.types import DecisionAction


class Decision(StoredSubject, ordering=("-created_at", "-id")):
    title: Mapped[str]
    question: Mapped[str] = mapped_column(Text)
    context: Mapped[str] = mapped_column(Text, default="")
    assessments: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    synthesis: Mapped[dict[str, Any] | None] = mapped_column(JSONB, default=None)
    recommendation: Mapped[DecisionAction | None]
    outcome: Mapped[DecisionAction | None]
    outcome_note: Mapped[str] = mapped_column(Text, default="")
    decided_at: Mapped[datetime | None]

    def __str__(self) -> str:
        return self.title

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
        await self.save()

    async def save_outcome(self, *, action: DecisionAction, note: str) -> None:
        self.outcome = action
        self.outcome_note = note
        self.decided_at = self.utc_now()
        await self.save()
