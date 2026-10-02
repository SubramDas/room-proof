"""Freeze a deterministic worst-gate ranking before any benchmark baseline."""


def rank_failed_gates(gates):
    """gates: [{id, direction: minimum|maximum, threshold, observed, affected}]."""
    ranked = []
    for gate in gates:
        threshold = gate["threshold"]
        observed = gate["observed"]
        if threshold <= 0 or gate["affected"] < 1:
            raise ValueError("threshold must be positive and affected count nonzero")
        if gate["direction"] == "minimum":
            gap = (threshold-observed)/threshold
        elif gate["direction"] == "maximum":
            gap = (observed-threshold)/threshold
        else:
            raise ValueError("direction must be minimum or maximum")
        if gap > 0:
            ranked.append({**gate, "relative_gap": gap})
    return sorted(ranked, key=lambda gate: (-gate["relative_gap"], -gate["affected"], gate["id"]))


def compare_fix(before, after, prediction):
    if before["id"] != after["id"] or before["threshold"] != after["threshold"] or before["direction"] != after["direction"]:
        raise ValueError("before/after gate definition changed")
    threshold = before["threshold"]
    if before["direction"] == "minimum":
        original_gap = threshold-before["observed"]
        closed = after["observed"]-before["observed"]
        passed = after["observed"] >= threshold
    elif before["direction"] == "maximum":
        original_gap = before["observed"]-threshold
        closed = before["observed"]-after["observed"]
        passed = after["observed"] <= threshold
    else:
        raise ValueError("invalid direction")
    if original_gap <= 0:
        raise ValueError("before gate was not failing")
    return {"gate_id": before["id"], "before": before["observed"],
            "predicted_after": prediction, "observed_after": after["observed"],
            "prediction_absolute_error": abs(after["observed"]-prediction),
            "gap_fraction_closed": closed/original_gap, "passed": passed,
            "meaningful_internal": closed/original_gap >= .25}
