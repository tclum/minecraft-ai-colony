from datetime import datetime

PRIORITY_RULES = [
    ("fallback behavior", 1),
    ("gatherwood", 1),
    ("gathering wood fails", 1),
    ("goal reset", 2),
    ("stale active goal", 2),
    ("workerloop", 3),
    ("loadmemory", 3),
    ("memory", 4),
    ("logging", 5),
    ("logger", 5),
    ("test", 7),
]

BAD_PHRASES = [
    "llm context",
    "updatellmcontext",
    "update llm context",
    "llm module",
    "currently has no",
    "may resume",
    "is not fully defined yet",
]

ACTION_STARTERS = [
    "implement",
    "add",
    "update",
    "define",
    "reset",
    "handle",
    "test",
    "review",
]

def parse_reviewed_actions(reviewed_actions_text: str):
    section = None
    approved = []
    needs_review = []
    rejected = []

    for raw_line in reviewed_actions_text.splitlines():
        line = raw_line.strip()

        if line == "## Approved":
            section = "approved"
            continue
        if line == "## Needs Review":
            section = "needs_review"
            continue
        if line == "## Rejected":
            section = "rejected"
            continue

        if not line.startswith("- "):
            continue

        item = line[2:].strip()

        if section == "approved":
            approved.append(item)
        elif section == "needs_review":
            needs_review.append(item)
        elif section == "rejected":
            rejected.append(item)

    return approved, needs_review, rejected

def score_action(action: str) -> int:
    lower = action.lower()
    for phrase, score in PRIORITY_RULES:
        if phrase in lower:
            return score
    return 99

def clean_action(action: str) -> str:
    a = action.strip()

    replacements = [
        ("**Implement a fallback behavior for `gatherWood`**:", "Implement fallback behavior for gatherWood:"),
        ("**Implement Goal Reset Behavior**:", "Implement goal reset behavior:"),
        ("**Stale Active Goal**:", "Address stale active goal:"),
        ("**No Fallback Behavior**:", "Address missing fallback behavior:"),
        ("**Goal Reset Behavior**:", "Address goal reset behavior:"),
    ]

    for old, new in replacements:
        a = a.replace(old, new)

    return a.strip()

def dedupe_keep_order(items):
    seen = set()
    out = []
    for item in items:
        normalized = item.lower().strip()
        if normalized not in seen:
            seen.add(normalized)
            out.append(item)
    return out

def is_actionable(action: str) -> bool:
    lower = action.lower().strip()

    if any(bad in lower for bad in BAD_PHRASES):
        return False

    if any(lower.startswith(starter) for starter in ACTION_STARTERS):
        return True

    if "`bots/" in action or "bots/" in action:
        return True

    return False

def build_next_actions(reviewed_actions_text: str) -> str:
    approved, needs_review, rejected = parse_reviewed_actions(reviewed_actions_text)

    approved = dedupe_keep_order([clean_action(x) for x in approved if "no automatically" not in x.lower()])
    needs_review = dedupe_keep_order([clean_action(x) for x in needs_review if "no automatically" not in x.lower()])

    approved = [x for x in approved if is_actionable(x)]
    needs_review = [x for x in needs_review if is_actionable(x)]

    ranked = sorted(approved, key=score_action)

    top_actions = ranked[:5]
    review_actions = needs_review[:3]

    if not top_actions:
        top_actions = ["No concrete approved actions available yet."]

    if not review_actions:
        review_actions = ["No review-needed actions selected."]

    return f"""# Next Actions

Generated: {datetime.now().isoformat()}

## Priority Execution Order
""" + "\n".join(f"{i+1}. {item}" for i, item in enumerate(top_actions)) + """

## Secondary / Review Queue
""" + "\n".join(f"- {item}" for item in review_actions) + """

## Notes
- Execute approved actions first.
- Ignore invented modules or APIs that do not exist in the codebase.
- After changes are made, rerun the orchestrator and compare the new report, plan, patch, and reviewed actions.
"""