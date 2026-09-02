from druks.agents import Agent
from druks.apps import App

from druks_panel.contracts import AdvisorAssessment, ModeratorSynthesis


class Panel(App):
    name = "panel"
    icon = "message-square"
    description = "Pressure-tests a decision, then parks for the human call."
    navigation = ["decisions"]

    opportunity = Agent(
        prompt="panel/opportunity.md",
        contract=AdvisorAssessment,
        description="Finds the upside, leverage, and strategic option value.",
    )
    risk = Agent(
        prompt="panel/risk.md",
        contract=AdvisorAssessment,
        description="Finds failure modes, hidden costs, and irreversible exposure.",
    )
    execution = Agent(
        prompt="panel/execution.md",
        contract=AdvisorAssessment,
        description="Tests whether the decision can be executed with the available means.",
    )
    moderator = Agent(
        prompt="panel/moderator.md",
        contract=ModeratorSynthesis,
        description="Synthesizes the panel without erasing disagreement.",
    )
