from druks_panel.contracts import AdvisorAssessment, ModeratorSynthesis


def test_advisor_assessment_renders_a_markdown_artifact():
    assessment = AdvisorAssessment(
        perspective="risk",
        position="yes_with_conditions",
        headline="The downside is bounded if the launch is staged.",
        rationale=["A pilot limits exposure."],
        uncertainties=["Support demand is unknown."],
        confidence=72,
    )

    artifact = assessment.get_artifact()

    assert artifact["kind"] == "markdown"
    assert artifact["title"] == "Risk assessment"
    assert "Support demand is unknown." in artifact["content"]


def test_moderator_synthesis_renders_the_recommendation():
    synthesis = ModeratorSynthesis(
        recommendation="revise",
        summary="The opportunity is real, but the first scope is too broad.",
        common_ground=["A smaller test preserves option value."],
        tradeoffs=["Speed versus learning quality."],
        questions_to_resolve=["Who owns the pilot?"],
        next_step="Define a two-week pilot.",
    )

    artifact = synthesis.get_artifact()

    assert artifact["title"] == "Panel synthesis"
    assert "Recommendation: Revise" in artifact["content"]
