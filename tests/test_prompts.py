from druks.prompts import render_prompt


async def test_panel_prompt_renders_from_the_installed_package(druks_without_remote_config):
    prompt = await render_prompt(
        "panel/opportunity.md",
        title="Launch the pilot",
        question="Should we launch in September?",
        context="Two weeks of capacity are available.",
    )

    assert "You are the opportunity advisor" in prompt
    assert "Should we launch in September?" in prompt
