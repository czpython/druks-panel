from druks_panel.models import Decision


async def test_decision_records_the_panel_and_human_outcome(druks_db):
    decision = await Decision.create(
        title="Launch the pilot",
        question="Should we launch the pilot in September?",
        context="The team has two weeks of capacity.",
    )
    assessment = {
        "perspective": "opportunity",
        "position": "strong_yes",
        "headline": "The pilot creates useful evidence.",
        "rationale": ["It tests willingness to pay."],
        "uncertainties": ["Conversion is unknown."],
        "confidence": 80,
    }
    synthesis = {
        "recommendation": "proceed",
        "summary": "Run a bounded pilot.",
        "common_ground": ["Keep it small."],
        "tradeoffs": ["Speed versus polish."],
        "questions_to_resolve": ["What is the stop condition?"],
        "next_step": "Name the first cohort.",
    }

    await decision.save_panel(
        assessments=[assessment],
        synthesis=synthesis,
        recommendation="proceed",
    )
    await decision.save_outcome(action="proceed", note="Cap the cohort at five teams.")

    saved = await Decision.get(decision.id)
    assert saved.assessments == [assessment]
    assert saved.synthesis == synthesis
    assert saved.outcome == "proceed"
    assert saved.decided_at is not None
    assert saved.get_summary().label == "Launch the pilot"
