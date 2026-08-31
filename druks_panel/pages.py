from druks import ui
from druks.workflows import SubjectStatus

from druks_panel.contracts import AdvisorAssessment, ModeratorSynthesis
from druks_panel.models import Decision


def _run_word(status: SubjectStatus) -> ui.StatusValue:
    """Where Druks is with the deliberation. The read side ships the state. The
    panel writes the word and selects the tone."""
    if status.is_parked:
        return ui.StatusValue("your call", tone="warning")
    if status.is_running:
        return ui.StatusValue("deliberating", tone="active")
    if status.is_failed:
        return ui.StatusValue(status.failure or "failed", tone="danger")
    if status.state:
        return ui.StatusValue(str(status.state))
    return ui.StatusValue("not started")


def _action_word(action: str | None) -> ui.StatusValue:
    """A panel verdict, recommended or recorded."""
    if not action:
        return ui.StatusValue("none yet")
    if action == "proceed":
        return ui.StatusValue("proceed", tone="success")
    if action == "revise":
        return ui.StatusValue("revise", tone="warning")
    return ui.StatusValue("pass")


def _position_word(assessment: AdvisorAssessment) -> ui.StatusValue:
    """One advisor's stance."""
    if assessment.position == "no":
        return ui.StatusValue("no", tone="danger")
    if assessment.position == "uncertain":
        return ui.StatusValue("uncertain", tone="warning")
    return ui.StatusValue(assessment.position.replace("_", " "), tone="success")


def _advisors(decision: Decision) -> ui.Section:
    if not decision.assessments:
        return ui.Section(
            title="The advisors",
            blocks=[ui.Text("Each advisor reports here when it finishes.")],
        )
    assessments = [AdvisorAssessment.model_validate(item) for item in decision.assessments]
    return ui.Section(
        title="The advisors",
        blocks=[
            ui.Columns(
                [
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
                ]
            )
        ],
    )


def _synthesis(decision: Decision) -> ui.Section:
    if not decision.synthesis:
        return ui.Section(
            title="The synthesis",
            blocks=[ui.Text("The moderator writes this after every advisor reports.")],
        )
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


def _the_call(decision: Decision, status: SubjectStatus) -> ui.Section:
    """The human gate: the form while the run waits on it, the record after."""
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
                ui.Quote(decision.outcome_note or "No note was left."),
            ],
        )
    if not status.is_parked:
        return ui.Section(
            title="The call",
            blocks=[ui.Text("The run parks here after the moderator reports.")],
        )
    return ui.Section(
        title="The call",
        blocks=[
            ui.Form(
                description="The run stays parked until you record the outcome.",
                fields=[
                    ui.RadioField(
                        name="action",
                        label="Outcome",
                        options=[
                            ui.Option("Proceed", value="proceed"),
                            ui.Option("Revise", value="revise"),
                            ui.Option("Pass", value="pass"),
                        ],
                        is_required=True,
                    ),
                    ui.TextAreaField(
                        name="note",
                        label="Note",
                        rows=3,
                        help_text="What the record must say about this call.",
                    ),
                ],
                action=ui.Action(
                    label="Record the decision",
                    operation="record_outcome",
                    arguments={"decision_id": decision.id},
                    tone="primary",
                ),
            )
        ],
    )


@ui.page("/")
async def decisions():
    recent = await Decision.list_recent()
    # One read for the whole board, not one for each row.
    statuses = await Decision.get_statuses([decision.id for decision in recent])
    return ui.Page(
        "Decisions",
        description="Every question this panel has weighed.",
        # The board follows the subject type, so a run that moves anywhere
        # redraws the table.
        follows=Decision,
        blocks=[
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
                                    decision.title,
                                    page="decision",
                                    arguments={"decision_id": str(decision.id)},
                                ),
                            ),
                            _run_word(statuses[str(decision.id)]),
                            _action_word(decision.recommendation),
                            _action_word(decision.outcome),
                            ui.TimeValue(decision.created_at),
                        ]
                    )
                    for decision in recent
                ],
                empty_text="No decision has gone to the panel yet.",
            )
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


@ui.page("/decisions/{decision_id}")
async def decision(decision_id: int):
    found = await Decision.get(decision_id)
    if not found:
        return ui.Page(
            f"Decision {decision_id}",
            blocks=[
                ui.EmptyState(
                    "No such decision",
                    actions=[ui.Link("Decisions", page="decisions")],
                )
            ],
        )
    status = await found.get_status()
    return ui.Page(
        found.title,
        description=found.question,
        # The deliberation is what an operator watches, so the whole page redraws
        # as each advisor lands. A parked run publishes nothing until it is
        # answered, so the form below keeps what the operator typed.
        follows=found,
        blocks=[
            ui.Facts(
                [
                    ui.Fact("Panel", value=_run_word(status)),
                    ui.Fact("Recommends", value=_action_word(found.recommendation)),
                    ui.Fact("Outcome", value=_action_word(found.outcome)),
                    ui.Fact("Opened", value=ui.TimeValue(found.created_at)),
                ]
            ),
            ui.Section(
                title="Context",
                blocks=[ui.Markdown(found.context or "No context was given.")],
            ),
            _advisors(found),
            _synthesis(found),
            _the_call(found, status),
            ui.Link("Everything Druks did about this decision", subject=found),
        ],
    )
