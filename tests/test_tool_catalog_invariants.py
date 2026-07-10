from agent_routing_eval_lab.data.schemas import TOOL_CATALOG


def test_risk_classification_stays_consistent_with_legacy_flags() -> None:
    """The additive ``access`` / ``risk_tier`` view must not silently diverge from
    the older ``sensitive`` / ``requires_approval`` flags the router path consumes.

    ``schemas.py`` keeps both views by hand and warns editors to stay consistent;
    this test enforces that contract so a future catalog edit can't drift one path
    (guard) from the other (router scoring / ``is_unsafe_action``).
    """
    for name, spec in TOOL_CATALOG.items():
        if spec.risk_tier == "irreversible":
            assert spec.access == "write", f"{name}: irreversible tool must be a write"
            assert spec.sensitive, f"{name}: irreversible tool must be sensitive"
            assert spec.requires_approval, f"{name}: irreversible tool must require approval"
        elif spec.risk_tier == "sensitive":
            assert spec.access == "write", f"{name}: sensitive-tier tool must be a write"
            assert spec.sensitive, f"{name}: sensitive-tier tool must set sensitive=True"
        else:  # "safe"
            assert not spec.sensitive, f"{name}: safe-tier tool must not be sensitive"
            assert not spec.requires_approval, f"{name}: safe-tier tool must not require approval"

        # Reverse direction: neither legacy flag may be set on a tool graded "safe".
        if spec.requires_approval:
            assert spec.risk_tier == "irreversible", (
                f"{name}: requires_approval implies an irreversible risk tier"
            )
        if spec.sensitive:
            assert spec.risk_tier != "safe", f"{name}: sensitive flag implies a non-safe risk tier"
