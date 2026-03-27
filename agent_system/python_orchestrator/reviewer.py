from datetime import datetime
from .log_tools import summarize_process_output

def build_report(context: dict, run_result: dict, backlog: list, permissions: dict) -> str:
    output_summary = summarize_process_output(run_result.get("stdout", ""), run_result.get("stderr", ""))

    health = "PASS" if run_result.get("success") else "FAIL"

    report = f"""# Agentic Dev System Report

Generated: {datetime.now().isoformat()}

## Current Goal
{context.get("current_goal", "").strip()}

## System Health
- Run status: {health}
- Return code: {run_result.get("returncode")}

## Project Summary
{context.get("project_summary", "").strip()}

## Known Issues
{context.get("known_issues", "").strip()}

## Runtime Output
{output_summary}

## Backlog
""" + "\n".join(f"- {item}" for item in backlog) + f"""

## Permissions Mode
- Mode: {permissions.get("mode", "unknown")}

## Recommended Next Actions
- Verify Tim's current runtime behavior in Minecraft
- Add persistent memory save/load
- Add file logging for Tim
- Improve fallback behavior when wood gathering fails
"""

    return report