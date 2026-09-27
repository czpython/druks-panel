from druks import ui

from druks_panel.contracts import AdvisorAssessment, ModeratorSynthesis
from druks_panel.models import Decision


def _action_word(action: str | None) -> ui.StatusValue:
    """A panel verdict, recommended or recorded."""
    if action == "proceed":
        return ui.StatusValue("proceed", tone="success")
    if action == "revise":
        return ui.StatusValue("revise", tone="warning")
    if action == "pass":
        return ui.StatusValue("pass")
    return ui.StatusValue("none yet")


def _position_word(assessment: AdvisorAssessment) -> ui.StatusValue:
    if assessment.position == "no":
        return ui.StatusValue("no", tone="danger")
    if assessment.position == "uncertain":
        return ui.StatusValue("uncertain", tone="warning")
    return ui.StatusValue(assessment.position.replace("_", " "), tone="success")


def _synthesis(decision: Decision) -> ui.Section:
    if decision.synthesis:
        synthesis = ModeratorSynthesis.model_validate(decision.synthesis)
        return ui.Section(
            title="The synthesis",
            blocks=[
                ui.Callout(synthesis.summary, title=f"Recommends: {synthesis.recommendation}"),
                ui.List(
                    [ui.TextValue(item) for item in synthesis.common_ground],
                    title="Common ground",
                ),
                ui.List([ui.TextValue(item) for item in synthesis.tradeoffs], title="Tradeoffs"),
                ui.List(
                    [ui.TextValue(item) for item in synthesis.questions_to_resolve],
                    title="Questions to resolve",
                ),
                ui.Facts([ui.Fact("Next step", value=ui.TextValue(synthesis.next_step))]),
            ],
        )
    return ui.Section(
        title="The synthesis",
        blocks=[ui.Text("The moderator writes this after every advisor reports.")],
    )


def _human_call(decision: Decision) -> ui.Section:
    """The human gate: the controls while the run waits, the record after."""
    if decision.outcome:
        return ui.Section(
            title="The call",
            blocks=[
                ui.Facts(
                    [
                        ui.Fact("Outcome", value=_action_word(decision.outcome)),
                        ui.Fact("Recorded", value=ui.TimeValue(decision.decided_at)),
                    ]
                ),
                ui.Quote(decision.outcome_note or "Nobody left a note."),
            ],
        )
    return ui.Section(
        title="The call",
        blocks=[
            ui.Text("After the moderator reports, the run waits here for your call."),
            ui.GateControls(decision),
        ],
    )


@ui.page("/")
async def decisions():
    recent = await Decision.all()
    return ui.Page(
        "Decisions",
        description="Every question this panel has weighed.",
        follows=Decision,
        blocks=[
            ui.Link("New decision", page="new_decision"),
            ui.Table(
                columns=[
                    ui.TableColumn("Decision"),
                    ui.TableColumn("Panel"),
                    ui.TableColumn("Recommends"),
                    ui.TableColumn("Outcome"),
                    ui.TableColumn("Opened", align="end"),
                ],
                rows=[
                    ui.TableRow(
                        [
                            ui.TextValue(
                                decision.title,
                                description=decision.question,
                                link=ui.Link(
                                    page="decision", arguments={"decision_id": decision.id}
                                ),
                            ),
                            ui.SubjectStatus(decision, working="deliberating"),
                            _action_word(decision.recommendation),
                            _action_word(decision.outcome),
                            ui.TimeValue(decision.created_at),
                        ]
                    )
                    for decision in recent
                ],
                empty=ui.EmptyState("No decision has gone to the panel yet."),
            ),
        ],
    )


@ui.page("/decisions/new")
async def new_decision():
    return ui.Page(
        "New decision",
        description="Three advisors examine it. A moderator combines them. Then you decide.",
        blocks=[
            ui.Form(
                title="The decision",
                fields=[
                    ui.TextField(
                        name="title",
                        label="Title",
                        placeholder="Move billing to a monthly cycle.",
                        is_required=True,
                    ),
                    ui.TextAreaField(
                        name="question",
                        label="Question",
                        placeholder="Do we move every customer to monthly billing in Q4?",
                        is_required=True,
                        rows=3,
                    ),
                    ui.TextAreaField(
                        name="context",
                        label="Context",
                        rows=6,
                        help_text="Constraints, numbers, and what you already tried.",
                    ),
                ],
                action=ui.Action(
                    label="Start the panel",
                    operation="create_decision",
                    tone="primary",
                    link=ui.Link("Decisions", page="decisions"),
                ),
            )
        ],
    )


@ui.page("/decisions/{decision_id}", subject=Decision)
async def decision(decision_id: int):
    decision = await Decision.get(id=decision_id)
    assessments = [AdvisorAssessment.model_validate(item) for item in decision.assessments]
    return ui.Page(
        decision.title,
        description=decision.question,
        # The whole page follows: an operator watches each advisor land. A
        # parked run publishes nothing, so a redraw cannot wipe a half-written note.
        follows=decision,
        blocks=[
            ui.Facts(
                [
                    ui.Fact("Panel", value=ui.SubjectStatus(decision, working="deliberating")),
                    ui.Fact("Recommends", value=_action_word(decision.recommendation)),
                    ui.Fact("Outcome", value=_action_word(decision.outcome)),
                    ui.Fact("Opened", value=ui.TimeValue(decision.created_at)),
                ]
            ),
            ui.Section(
                title="Context",
                blocks=[ui.Markdown(decision.context or "Nobody added context.")],
            ),
            ui.Cards(
                title="The advisors",
                cards=[
                    ui.Card(
                        title=assessment.perspective.title(),
                        description=assessment.headline,
                        blocks=[
                            ui.Facts(
                                [
                                    ui.Fact("Position", value=_position_word(assessment)),
                                    ui.Fact(
                                        "Confidence",
                                        value=ui.NumberValue(assessment.confidence, unit="%"),
                                    ),
                                ]
                            ),
                            ui.List(
                                [ui.TextValue(item) for item in assessment.rationale],
                                title="Rationale",
                            ),
                            ui.List(
                                [ui.TextValue(item) for item in assessment.uncertainties],
                                title="Uncertainties",
                            ),
                        ],
                    )
                    for assessment in assessments
                ],
                empty=ui.EmptyState(
                    "No assessment yet",
                    description="Each advisor reports here when it finishes.",
                ),
            ),
            _synthesis(decision),
            _human_call(decision),
        ],
    )
