import json
from .model_client import call_model
from .config import MODEL_NAME

CODER_SYSTEM_PROMPT = """You are an expert software engineering assistant.

Your task:
- Read the active issue
- Read the latest runtime report
- Read the selected source files
- Read the validator failure reasons and validator expectation summary
- Read the recent attempt history for this issue
- Propose a minimal patch that targets ONLY the editable files listed in the issue

Rules:
- Return valid JSON only
- Do not include markdown fences
- Only modify files explicitly listed as editable
- Keep changes minimal and targeted
- Do not redesign the architecture
- Do not mention orchestrator timeouts as bot bugs
- Prefer full-file replacements for the changed files
- Align log strings and control flow with the validator expectations
- Avoid repeating patch patterns that already failed in recent attempt history

JSON format:
{
  "summary": "short summary",
  "files": [
    {
      "path": "relative/path.js",
      "content": "full new file content here"
    }
  ]
}
"""

def build_coder_prompt(
    issue: dict,
    runtime_report: str,
    source_files: dict,
    validator_reasons: list[str],
    validator_expectation_summary: str,
    attempt_history: str,
) -> str:
    payload = {
        "issue": issue,
        "validator_failure_reasons": validator_reasons,
        "validator_expectation_summary": validator_expectation_summary,
        "recent_attempt_history": attempt_history,
        "latest_runtime_report": runtime_report,
        "source_files": source_files,
    }
    return json.dumps(payload, indent=2)

def generate_patch_json(
    issue: dict,
    runtime_report: str,
    source_files: dict,
    validator_reasons: list[str],
    validator_expectation_summary: str,
    attempt_history: str,
) -> dict:
    prompt = build_coder_prompt(
        issue=issue,
        runtime_report=runtime_report,
        source_files=source_files,
        validator_reasons=validator_reasons,
        validator_expectation_summary=validator_expectation_summary,
        attempt_history=attempt_history,
    )

    raw = call_model(
        CODER_SYSTEM_PROMPT,
        prompt,
        MODEL_NAME,
        json_mode=True
    )

    return json.loads(raw)