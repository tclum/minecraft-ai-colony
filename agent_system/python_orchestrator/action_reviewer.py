from datetime import datetime

APPROVE_HINTS = [
    "fallback behavior",
    "no logs are nearby",
    "no logs found nearby",
    "reset the goal status",
    "stale active goal",
    "logging",
    "persistent memory",
    "scout_area",
    "collect_wood",
    "goal reset",
    "falling back to exploration",
]

REJECT_HINTS = [
    "25 seconds",
    "25 second",
    "timed out after 25",
    "handle timeouts",
    "timeout mechanism",
    "timeouterror",
    "orchestrator's timeout",
    "orchestrator timeout",
    "econreset",
    "ecconnreset",
    "separate thread",
    "separate process to save and load memory",
]

REVIEW_HINTS = [
    "more robust memory persistence",
    "inactivity timestamps",
    "movement speed",
    "logger file name timestamp",
    "try-catch block around the workerloop",
]

def split_lines(text: str):
    return [line.strip() for line in text.splitlines() if line.strip()]

def extract_candidate_actions(plan_text: str, patch_text: str):
    candidates = []

    for line in split_lines(plan_text):
        if line.startswith("- ") or line.startswith("* "):
            candidates.append(line[2:].strip())
        elif len(line) > 3 and line[0].isdigit() and ". " in line:
            candidates.append(line.split(". ", 1)[1].strip())

    for line in split_lines(patch_text):
        if line.startswith("- "):
            candidates.append(line[2:].strip())

    seen = set()
    unique = []
    for item in candidates:
        if item not in seen:
            seen.add(item)
            unique.append(item)

    return unique

def classify_line(line: str) -> str:
    lower = line.lower()

    matched_reject = any(hint in lower for hint in REJECT_HINTS)
    matched_approve = any(hint in lower for hint in APPROVE_HINTS)
    matched_review = any(hint in lower for hint in REVIEW_HINTS)

    if matched_reject and matched_approve:
        return "needs_review"

    if matched_reject:
        return "rejected"

    if matched_approve:
        return "approved"

    if matched_review:
        return "needs_review"

    return "needs_review"

def build_reviewed_actions(plan_text: str, patch_text: str) -> str:
    actions = extract_candidate_actions(plan_text, patch_text)

    approved = []
    needs_review = []
    rejected = []

    for action in actions:
        label = classify_line(action)
        if label == "approved":
            approved.append(action)
        elif label == "rejected":
            rejected.append(action)
        else:
            needs_review.append(action)

    if not approved:
        approved.append("No automatically approved actions yet.")

    if not needs_review:
        needs_review.append("No review-needed actions identified.")

    if not rejected:
        rejected.append("No automatically rejected actions identified.")

    return f"""# Reviewed Actions

Generated: {datetime.now().isoformat()}

## Approved
""" + "\n".join(f"- {item}" for item in approved) + """

## Needs Review
""" + "\n".join(f"- {item}" for item in needs_review) + """

## Rejected
""" + "\n".join(f"- {item}" for item in rejected) + """
"""