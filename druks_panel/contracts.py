from druks.agents import AgentOutput
from pydantic import Field

from druks_panel.types import AdvisorPerspective, AdvisorPosition, DecisionAction


class AdvisorAssessment(AgentOutput):
    perspective: AdvisorPerspective
    position: AdvisorPosition
    headline: str
    rationale: list[str]
    uncertainties: list[str]
    confidence: int = Field(ge=0, le=100)

    def get_artifact(self) -> dict[str, str]:
        rationale = "\n".join(f"- {item}" for item in self.rationale)
        uncertainties = "\n".join(f"- {item}" for item in self.uncertainties)
        content = (
            f"# {self.perspective.title()} assessment\n\n"
            f"**{self.headline}**\n\n"
            f"Position: `{self.position}` · Confidence: {self.confidence}%\n\n"
            f"## Rationale\n\n{rationale}\n\n"
            f"## Uncertainties\n\n{uncertainties}"
        )
        return {
            "kind": "markdown",
            "title": f"{self.perspective.title()} assessment",
            "content": content,
        }


class ModeratorSynthesis(AgentOutput):
    recommendation: DecisionAction
    summary: str
    common_ground: list[str]
    tradeoffs: list[str]
    questions_to_resolve: list[str]
    next_step: str

    def get_artifact(self) -> dict[str, str]:
        common_ground = "\n".join(f"- {item}" for item in self.common_ground)
        tradeoffs = "\n".join(f"- {item}" for item in self.tradeoffs)
        questions = "\n".join(f"- {item}" for item in self.questions_to_resolve)
        content = (
            "# Panel synthesis\n\n"
            f"**Recommendation: {self.recommendation.title()}**\n\n"
            f"{self.summary}\n\n"
            f"## Common ground\n\n{common_ground}\n\n"
            f"## Tradeoffs\n\n{tradeoffs}\n\n"
            f"## Questions to resolve\n\n{questions}\n\n"
            f"## Next step\n\n{self.next_step}"
        )
        return {"kind": "markdown", "title": "Panel synthesis", "content": content}
