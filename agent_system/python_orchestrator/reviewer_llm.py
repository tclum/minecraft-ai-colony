import json
from .model_client import call_model
from .config import REVIEW_MODEL_NAME, REVIEW_PROVIDER

REVIEWER_SYSTEM_PROMPT = """You are a strict patch reviewer for a Minecraft AI bot project.

You are reviewing a proposed patch before it is applied.

Your job:
- decide whether the patch should be approved, revised, or rejected
- ensure it only addresses the active issue
- ensure it only touches allowed editable files
- check whether the patch appears likely to satisfy the success criteria
- check whether the patch introduces obvious type, state, or control-flow mismatches
- use the validator failures and recent attempt history to detect repeated bad patch patterns
- prefer minimal targeted changes

Rules:
- return valid JSON only
- do not include markdown fences
- do not rewrite the patch
- be strict
- if the patch changes unrelated behavior, choose "revise" or "reject"
- if the patch repeats a previously unsuccessful pattern, choose "revise" or "reject"
- if the patch appears dangerous or mismatched to the issue, choose "reject"

JSON format:
{
  "decision": "approve" | "revise" | "reject",
  "reason": "short explanation",
  "concerns": ["..."],
  "required_changes": ["..."]
}
"""

def build_review_prompt(
    issue: dict,
    patch_data: dict,
    source_files: dict,
    runtime_report: str,
    attempt_history: str,
    validator_reasons: list[str],
    validator_expectation_summary: str,
) -> str:
    payload = {
        "issue": issue,
        "validator_failure_reasons": validator_reasons,
        "validator_expectation_summary": validator_expectation_summary,
        "recent_attempt_history": attempt_history,
        "latest_runtime_report": runtime_report,
        "proposed_patch": patch_data,
        "current_files": source_files,
    }
    return json.dumps(payload, indent=2)

def review_patch(
    issue: dict,
    patch_data: dict,
    source_files: dict,
    runtime_report: str,
    attempt_history: str,
    validator_reasons: list[str],
    validator_expectation_summary: str,
) -> dict:
    prompt = build_review_prompt(
        issue=issue,
        patch_data=patch_data,
        source_files=source_files,
        runtime_report=runtime_report,
        attempt_history=attempt_history,
        validator_reasons=validator_reasons,
        validator_expectation_summary=validator_expectation_summary,
    )

    raw = call_model(
        REVIEWER_SYSTEM_PROMPT,
        prompt,
        REVIEW_MODEL_NAME,
        json_mode=True,
        provider=REVIEW_PROVIDER
    )

    try:
        return json.loads(raw)
    except Exception:
        return {
            "decision": "reject",
            "reason": "invalid_json_from_reviewer",
            "concerns": [raw],
            "required_changes": []
        }