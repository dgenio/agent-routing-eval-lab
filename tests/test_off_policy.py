from agent_routing_eval_lab.evaluation.off_policy import estimate_off_policy


def _row(chosen: str, propensity: float, reward: float) -> dict:
    return {"chosen_tool": chosen, "propensity_score": propensity, "reward": reward}


def test_ips_and_snips_match_closed_form() -> None:
    # Row A: candidate reproduces logged action, w = 1/0.5 = 2, contributes 2*1.0.
    # Row B: candidate reproduces logged action, w = 1/1.0 = 1, contributes 1*0.0.
    logged = [_row("t1", 0.5, 1.0), _row("t2", 1.0, 0.0)]
    candidates = ["t1", "t2"]

    estimate = estimate_off_policy(logged, candidates, min_match_rate=0.0, min_effective_sample_size=0.0)

    assert estimate.available is True
    assert estimate.matched == 2
    assert estimate.n == 2
    # IPS = (2*1.0 + 1*0.0) / 2 = 1.0
    assert estimate.ips == 1.0
    # SNIPS = (2*1.0 + 1*0.0) / (2 + 1) = 0.6667
    assert round(estimate.snips, 4) == 0.6667


def test_no_overlap_yields_zero_ips_flagged_low_confidence() -> None:
    logged = [_row("t1", 0.5, 1.0), _row("t2", 0.5, 1.0)]
    candidates = ["other", "other"]  # candidate never reproduces a logged action

    estimate = estimate_off_policy(logged, candidates)

    assert estimate.available is True
    assert estimate.ips == 0.0
    assert estimate.matched == 0
    assert estimate.low_confidence is True


def test_unavailable_when_logs_lack_signal() -> None:
    logged = [{"chosen_tool": "t1"}, {"chosen_tool": "t2"}]  # no propensity/reward
    candidates = ["t1", "t2"]

    estimate = estimate_off_policy(logged, candidates)

    assert estimate.available is False
    assert estimate.ips is None
    assert estimate.snips is None
    assert "unavailable" in estimate.reason


def test_thin_overlap_is_low_confidence() -> None:
    # 20 rows, candidate matches only one → match_rate 5% < default 15% threshold.
    logged = [_row(f"t{i}", 0.5, 1.0) for i in range(20)]
    candidates = ["t0"] + [f"x{i}" for i in range(1, 20)]

    estimate = estimate_off_policy(logged, candidates)

    assert estimate.available is True
    assert estimate.matched == 1
    assert estimate.low_confidence is True
