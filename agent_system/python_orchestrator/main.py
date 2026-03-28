from datetime import datetime
import json
from rich import print

from .task_manager import load_context, load_key_source_files, load_selected_source_files
from .memory_store import load_backlog, load_permissions
from .runner import run_tim
from .reviewer import build_report
from .planner import generate_plan, generate_patch_proposal
from .action_reviewer import build_reviewed_actions
from .next_action_builder import build_next_actions
from .issue_loader import load_active_issue, load_edit_permissions
from .validator import validate_issue
from .coder import generate_patch_json
from .patch_applier import verify_patch_paths, apply_patch_files
from .backup_manager import backup_original_once
from .file_tools import write_text_file, append_text_file, read_tail_lines, read_text_file
from .reviewer_llm import review_patch

from .config import (
    REPORT_FILE,
    LLM_PLAN_FILE,
    PROPOSED_PATCH_FILE,
    REVIEWED_ACTIONS_FILE,
    NEXT_ACTIONS_FILE,
    ATTEMPT_HISTORY_FILE,
    PATCH_REVIEW_FILE,
)

def write_attempt_history(issue_title: str, attempt_num: int, status: str, notes: list[str]):
    lines = [
        f"\n## {datetime.now().isoformat()} - Attempt {attempt_num}",
        f"- Issue: {issue_title}",
        f"- Status: {status}",
    ]
    for note in notes:
        lines.append(f"- Note: {note}")
    lines.append("")
    append_text_file(ATTEMPT_HISTORY_FILE, "\n".join(lines))

def run_snapshot(context, backlog, permissions, runtime_seconds):
    run_result = run_tim(timeout_seconds=runtime_seconds)
    report = build_report(context, run_result, backlog, permissions)
    write_text_file(REPORT_FILE, report)

    source_files = load_key_source_files()
    merged_context = {**context, "last_report": report}

    plan = generate_plan(merged_context, source_files)
    write_text_file(LLM_PLAN_FILE, plan)

    patch_proposal = generate_patch_proposal(merged_context, source_files)
    write_text_file(PROPOSED_PATCH_FILE, patch_proposal)

    reviewed_actions = build_reviewed_actions(plan, patch_proposal)
    write_text_file(REVIEWED_ACTIONS_FILE, reviewed_actions)

    next_actions = build_next_actions(reviewed_actions)
    write_text_file(NEXT_ACTIONS_FILE, next_actions)

    return report, next_actions

def extract_current_issue_history(issue_title: str, max_lines: int = 120) -> str:
    raw = read_text_file(ATTEMPT_HISTORY_FILE)
    if not raw.strip():
        return ""

    lines = raw.splitlines()
    kept_blocks = []
    current_block = []

    for line in lines:
        if line.startswith("## "):
            if current_block:
                block_text = "\n".join(current_block)
                if f"- Issue: {issue_title}" in block_text:
                    kept_blocks.append(block_text)
            current_block = [line]
        else:
            if current_block:
                current_block.append(line)

    if current_block:
        block_text = "\n".join(current_block)
        if f"- Issue: {issue_title}" in block_text:
            kept_blocks.append(block_text)

    filtered = "\n\n".join(kept_blocks)
    filtered_lines = filtered.splitlines()
    return "\n".join(filtered_lines[-max_lines:])

def build_validator_expectation_summary(issue: dict, validation_reasons: list[str]) -> str:
    lines = [
        f"Issue title: {issue.get('title', '')}",
        "Success criteria:",
    ]
    for item in issue.get("success_criteria", []):
        lines.append(f"- {item}")

    lines.append("Current validator failure reasons:")
    if validation_reasons:
        for item in validation_reasons:
            lines.append(f"- {item}")
    else:
        lines.append("- None")

    lines.append("Reviewer instruction:")
    lines.append("- Approve only if the patch appears likely to satisfy the listed success criteria and address the current validator failure reasons.")
    lines.append("- Reject or request revision if the patch repeats a previously unsuccessful pattern.")
    return "\n".join(lines)

def main():
    print("[bold cyan]Agentic Dev System v3.1 starting...[/bold cyan]")

    context = load_context()
    backlog = load_backlog()
    permissions = load_permissions()
    issue = load_active_issue()
    edit_permissions = load_edit_permissions()

    runtime_seconds = issue.get("runtime_seconds", 25)

    print(f"[yellow]Active issue:[/yellow] {issue['title']}")
    print(f"[yellow]Max attempts:[/yellow] {issue['max_attempts']}")
    print(f"[yellow]Runtime seconds per attempt:[/yellow] {runtime_seconds}")

    for attempt in range(1, issue["max_attempts"] + 1):
        print(f"\n[bold]Attempt {attempt}[/bold]")

        report, next_actions = run_snapshot(context, backlog, permissions, runtime_seconds)
        validation = validate_issue(issue, report)

        if validation["passed"]:
            print("[bold green]Issue already solved.[/bold green]")
            write_attempt_history(issue["title"], attempt, "passed", ["Issue validated before patching"])
            return

        write_attempt_history(issue["title"], attempt, "not_passed_yet", validation["reasons"])

        editable_files = issue.get("editable_files", [])
        selected_files = load_selected_source_files(editable_files)

        recent_attempt_history = extract_current_issue_history(issue["title"], max_lines=120)
        validator_expectation_summary = build_validator_expectation_summary(issue, validation["reasons"])

        print("[yellow]Generating patch JSON...[/yellow]")
        patch_data = generate_patch_json(
            issue=issue,
            runtime_report=report,
            source_files=selected_files,
            validator_reasons=validation["reasons"],
            validator_expectation_summary=validator_expectation_summary,
            attempt_history=recent_attempt_history,
        )

        allowed = edit_permissions.get("auto_edit_allowed", [])
        ok, disallowed = verify_patch_paths(patch_data, allowed)

        if not ok:
            print("[bold red]Patch includes disallowed files.[/bold red]")
            write_attempt_history(issue["title"], attempt, "blocked", [f"Disallowed files: {disallowed}"])
            return

        print("[yellow]Reviewing patch with reviewer model...[/yellow]")

        recent_attempt_history = extract_current_issue_history(issue["title"], max_lines=120)
        validator_expectation_summary = build_validator_expectation_summary(issue, validation["reasons"])

        patch_review = review_patch(
            issue=issue,
            patch_data=patch_data,
            source_files=selected_files,
            runtime_report=report,
            attempt_history=recent_attempt_history,
            validator_reasons=validation["reasons"],
            validator_expectation_summary=validator_expectation_summary,
        )

        write_text_file(
            PATCH_REVIEW_FILE,
            json.dumps(patch_review, indent=2)
        )

        decision = patch_review.get("decision", "").lower()

        if decision == "reject":
            print("[bold red]Reviewer rejected patch.[/bold red]")
            write_attempt_history(
                issue["title"],
                attempt,
                "review_rejected",
                [patch_review.get("reason", "")]
                + patch_review.get("concerns", [])
                + patch_review.get("required_changes", [])
            )
            continue

        if decision == "revise":
            print("[yellow]Reviewer requested revision.[/yellow]")
            write_attempt_history(
                issue["title"],
                attempt,
                "review_revision_requested",
                [patch_review.get("reason", "")]
                + patch_review.get("concerns", [])
                + patch_review.get("required_changes", [])
            )
            continue

        print("[green]Reviewer approved patch.[/green]")
        write_attempt_history(
            issue["title"],
            attempt,
            "review_approved",
            [patch_review.get("reason", "approved")] + patch_review.get("concerns", [])
        )

        for rel_path in [item["path"] for item in patch_data.get("files", [])]:
            backed_up = backup_original_once(rel_path)
            if backed_up:
                write_attempt_history(
                    issue["title"],
                    attempt,
                    "backup_created",
                    [f"Original backup saved for {rel_path}"]
                )

        print("[yellow]Applying patch...[/yellow]")
        apply_patch_files(patch_data)
        write_attempt_history(
            issue["title"],
            attempt,
            "patch_applied",
            [f"Patched files: {[item['path'] for item in patch_data.get('files', [])]}"]
        )
        
        if validation["passed"]:
            print(f"[bold green]✅ Capability '{next_capability}' successfully implemented![/bold green]")

            registry = mark_capability_stable(
                registry,
                next_capability,
                f"Implemented by autonomous agent on {datetime.now().strftime('%Y-%m-%d')}"
            )
            save_registry(registry)
            consecutive_failures = 0

            # Restart Tim to pick up the new code
            restart_tim()

        # Alert on milestones
        if next_capability in MILESTONE_CAPABILITIES:
            write_alert(
                f"🏆 Major Milestone: {next_capability}",
                f"Tim has successfully implemented '{next_capability}'.\n"
                f"Total stable capabilities: {len(registry['capabilities'])}\n"
                f"Tim has been automatically restarted with the new code.\n"
                f"Completed on: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )

        report_after, _ = run_snapshot(context, backlog, permissions, runtime_seconds)
        validation_after = validate_issue(issue, report_after)

        if validation_after["passed"]:
            print("[bold green]Issue solved after patch.[/bold green]")
            write_attempt_history(issue["title"], attempt, "passed", ["Issue validated after patch"])
            return

        print("[yellow]Issue not solved yet. Continuing...[/yellow]")
        write_attempt_history(issue["title"], attempt, "retry_needed", validation_after["reasons"])

    print("[bold red]Max attempts reached without solving issue.[/bold red]")

if __name__ == "__main__":
    main()