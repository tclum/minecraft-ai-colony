def validate_issue(issue: dict, runtime_report: str) -> dict:
    text = runtime_report.lower()
    title = issue.get("title", "").lower()

    if "gather/pathfinding" in title or "gather" in title:
        passed = (
            "gather step failed:" in text
            and "pathfinding_failed" in text
            and "new goal: scout_area" in text
            and "workerloop error: inventorysnapshot.filter is not a function" not in text
        )

        reasons = []
        if "gather step failed:" not in text:
            reasons.append("Missing structured gather failure warning")
        if "pathfinding_failed" not in text:
            reasons.append("Missing structured pathfinding_failed result")
        if "new goal: scout_area" not in text:
            reasons.append("Missing replanning into scout_area after gather failure")
        if "workerloop error: inventorysnapshot.filter is not a function" in text:
            reasons.append("Type regression error still present")

        return {"passed": passed, "reasons": reasons}

    if "gather to build" in title or "build after collecting enough logs" in title:
        passed = (
            "new goal: build_column (reason: enough logs collected)" in text
            and 'next step chosen: {"type":"buildcolumn"' in text
            and 'executing step: {"type":"buildcolumn"' in text
        )

        reasons = []
        if "new goal: build_column (reason: enough logs collected)" not in text:
            reasons.append("Missing goal switch to build_column after enough logs")
        if 'next step chosen: {"type":"buildcolumn"' not in text:
            reasons.append("Missing buildColumn step selection")
        if 'executing step: {"type":"buildcolumn"' not in text:
            reasons.append("Missing buildColumn execution log")

        return {"passed": passed, "reasons": reasons}

    if "death" in title:
        passed = (
            "bot died." in text
            and "reset transient goal state after death" in text
            and "new goal:" in text
        )

        reasons = []
        if "bot died." not in text:
            reasons.append("Missing death log")
        if "reset transient goal state after death" not in text:
            reasons.append("Missing explicit death reset log")
        if "new goal:" not in text:
            reasons.append("Missing fresh goal selection after death")

        return {"passed": passed, "reasons": reasons}

    if "explore/pathfinding" in title or "explore" in title or "reachable positions" in title:
        passed = (
            "post-explore inventory:" in text
            and "explore step failed: pathfinding_failed (no path to the goal!)" not in text
            and "workerloop error: took to long to decide path to goal!" not in text
        )

        reasons = []
        if "post-explore inventory:" not in text:
            reasons.append("Missing successful explore completion log")
        if "explore step failed: pathfinding_failed (no path to the goal!)" in text:
            reasons.append("Explore is still choosing unreachable targets")
        if "workerloop error: took to long to decide path to goal!" in text:
            reasons.append("Generic workerLoop pathfinding error still present")

        return {"passed": passed, "reasons": reasons}

    if "inventory snapshot" in title or "log counting crash" in title:
        passed = (
            "workerloop error: inventorysnapshot.filter is not a function" not in text
            and "inventory snapshot:" in text
            and "current total log count:" in text
        )

        reasons = []
        if "workerloop error: inventorysnapshot.filter is not a function" in text:
            reasons.append("Inventory snapshot filter crash still present")
        if "inventory snapshot:" not in text:
            reasons.append("Missing inventory snapshot log output")
        if "current total log count:" not in text:
            reasons.append("Missing total log count output")

        return {"passed": passed, "reasons": reasons}

    if "more active" in title or "active between replans" in title:
        passed = (
            text.count('executing step: {"type":"explore"') + text.count('executing step: {"type":"gatherwood"}') >= 3
            and "workerloop error:" not in text
        )

        reasons = []
        step_count = text.count('executing step: {"type":"explore"') + text.count('executing step: {"type":"gatherwood"}')
        if step_count < 3:
            reasons.append("Too few visible step executions during runtime window")
        if "workerloop error:" in text:
            reasons.append("workerLoop error still present")

        return {"passed": passed, "reasons": reasons}

    if "combat" in title or "defense" in title or "attack" in title:
        passed = (
            "threat detected:" in text
            and ("target defeated" in text or "combat result:" in text)
            and "workerloop error:" not in text
        )

        reasons = []
        if "threat detected:" not in text:
            reasons.append("No threat detection logged")
        if "target defeated" not in text and "combat result:" not in text:
            reasons.append("No combat outcome logged")
        if "workerloop error:" in text:
            reasons.append("workerLoop error present during combat")

        return {"passed": passed, "reasons": reasons}

    if "flee" in title or "low health" in title:
        passed = (
            "flee result:" in text
            and "low health" in text
            and "workerloop error:" not in text
        )

        reasons = []
        if "flee result:" not in text:
            reasons.append("No flee outcome logged")
        if "low health" not in text:
            reasons.append("No low health trigger logged")

        return {"passed": passed, "reasons": reasons}

    if "prevent gather thrashing" in title or "gather enough logs" in title:
        log_progress = any(f"current total log count: {n}" in text for n in range(1, 20))
        build_switch = "new goal: build_column (reason: enough logs collected)" in text

        passed = (
            "post-gather inventory:" in text
            and log_progress
            and build_switch
        )

        reasons = []
        if "post-gather inventory:" not in text:
            reasons.append("Missing successful gather evidence")
        if not log_progress:
            reasons.append("Log count never increased above 0")
        if not build_switch:
            reasons.append("Missing switch to build_column after enough logs")

        return {"passed": passed, "reasons": reasons}

    return {
        "passed": False,
        "reasons": ["No validator rule implemented for this issue yet."]
    }