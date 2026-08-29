from druks_panel.app import Panel
from druks_panel.models import Decision


def test_panel_declares_its_public_surface():
    assert Panel.name == "panel"
    assert Panel.navigation == [("/panel", "decisions")]
    assert [agent.id for agent in Panel.agents()] == [
        "execution",
        "moderator",
        "opportunity",
        "risk",
    ]
    assert Decision.__tablename__ == "panel_decisions"
