from datetime import datetime
from rich import print

from .main import main as run_issue_loop
from .autonomous_planner import (
    load_registry,
    save_registry,
    pick_next_capability,
    generate_issue_for_capability,
    write_active_issue,
    mark_capability_stable,
    get_current_issue_title,
)
from .issue_loader import load_active_issue
from .validator import validate_issue
from .file_tools import read_text_file
from .config import REPORT_FILE
from .notifier import send_email_alert
import subprocess
import signal
import time
from pathlib import Path
from typing import Optional


MAX_CONSECUTIVE_FAILURES = 3
MILESTONE_CAPABILITIES = {"craft_wooden_pickaxe", "build_shelter", "craft_iron_tools"}
LOCK_FILE = Path("/tmp/tim.lock")
START_TIM_COMMAND = ["node", "agent_system/node_bridge/start_tim.js"]

def get_tim_pid() -> Optional[int]:
    try:
        if LOCK_FILE.exists():
            return int(LOCK_FILE.read_text().strip())
    except Exception:
        pass
    return None

def restart_tim():
    print("[bold yellow]Restarting Tim to apply patch...[/bold yellow]")

    # Kill existing Tim process
    pid = get_tim_pid()
    if pid:
        try:
            import os
            os.kill(pid, signal.SIGTERM)
            print(f"[yellow]Killed Tim process (PID {pid})[/yellow]")
            time.sleep(2)
        except ProcessLookupError:
            print("[yellow]Tim process already gone[/yellow]")
        except Exception as e:
            print(f"[red]Failed to kill Tim: {e}[/red]")

    # Clean up lockfile in case it wasn't removed
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except Exception:
        pass

    # Start fresh Tim process
    try:
        process = subprocess.Popen(
            START_TIM_COMMAND,
            cwd=str(ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print(f"[green]Tim restarted (PID {process.pid})[/green]")
        time.sleep(3)  # give Tim time to connect and spawn
    except Exception as e:
        print(f"[red]Failed to restart Tim: {e}[/red]")
        write_alert("❌ Tim Restart Failed", f"Could not restart Tim after patch.\nError: {e}")

def write_alert(subject: str, body: str = ""):
    if not body:
        body = subject
        subject = "Tim Agent Alert"
    send_email_alert(subject, body)


def autonomous_loop():
    print("[bold cyan]Autonomous Dev System starting...[/bold cyan]")
    print("[yellow]Tim will continuously develop new capabilities.[/yellow]")
    print("[yellow]You will be alerted by email on major milestones or repeated failures.[/yellow]\n")

    consecutive_failures = 0

    while True:
        registry = load_registry()
        next_capability = pick_next_capability(registry)

        if not next_capability:
            write_alert(
                "🎉 Roadmap Complete",
                "All roadmap capabilities are stable. Tim is fully developed!"
            )
            print("[bold green]Roadmap complete! All capabilities stable.[/bold green]")
            break

        print(f"\n[bold]Next capability to develop:[/bold] {next_capability}")

        # Generate and write the issue
        print("[yellow]Generating issue...[/yellow]")
        try:
            issue_text = generate_issue_for_capability(next_capability, registry)
        except Exception as e:
            print(f"[red]Failed to generate issue: {e}[/red]")
            consecutive_failures += 1
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                write_alert(
                    f"❌ Issue Generation Failing",
                    f"Failed to generate issue for '{next_capability}' {consecutive_failures} times.\nError: {e}"
                )
            continue

        write_active_issue(issue_text)
        print(f"[green]Issue written:[/green]\n{issue_text}\n")

        # Run the orchestrator loop on this issue
        try:
            run_issue_loop()
        except SystemExit:
            pass
        except Exception as e:
            print(f"[red]Orchestrator error: {e}[/red]")
            consecutive_failures += 1
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                write_alert(
                    f"❌ Orchestrator Failing on '{next_capability}'",
                    f"{consecutive_failures} consecutive orchestrator failures.\nError: {e}\nManual intervention may be needed."
                )
            continue

        # Check if the issue was solved
        try:
            issue = load_active_issue()
            report = read_text_file(REPORT_FILE)
            validation = validate_issue(issue, report)
        except Exception as e:
            print(f"[red]Validation error: {e}[/red]")
            consecutive_failures += 1
            continue

        if validation["passed"]:
            print(f"[bold green]✅ Capability '{next_capability}' successfully implemented![/bold green]")

            registry = mark_capability_stable(
                registry,
                next_capability,
                f"Implemented by autonomous agent on {datetime.now().strftime('%Y-%m-%d')}"
            )
            save_registry(registry)
            consecutive_failures = 0

            # Alert on milestones
            if next_capability in MILESTONE_CAPABILITIES:
                write_alert(
                    f"🏆 Major Milestone: {next_capability}",
                    f"Tim has successfully implemented '{next_capability}'.\n"
                    f"Total stable capabilities: {len(registry['capabilities'])}\n"
                    f"Completed on: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                )
            else:
                # Send a lighter confirmation for non-milestone capabilities
                write_alert(
                    f"✅ Capability Implemented: {next_capability}",
                    f"Tim successfully learned '{next_capability}'.\n"
                    f"Total stable capabilities: {len(registry['capabilities'])}"
                )

        else:
            print(f"[yellow]Capability '{next_capability}' not solved in this run.[/yellow]")
            print(f"Reasons: {validation['reasons']}")
            consecutive_failures += 1

            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                write_alert(
                    f"⚠️ Stuck on '{next_capability}'",
                    f"Failed {consecutive_failures} times in a row.\n"
                    f"Failure reasons:\n" + "\n".join(f"- {r}" for r in validation["reasons"]) +
                    f"\n\nSkipping and moving to next capability."
                )

                # Skip this capability rather than looping forever
                print(f"[yellow]Skipping '{next_capability}' after {consecutive_failures} failures.[/yellow]")
                registry = mark_capability_stable(
                    registry,
                    next_capability,
                    f"Skipped after {consecutive_failures} failures on {datetime.now().strftime('%Y-%m-%d')} — needs manual review"
                )
                save_registry(registry)
                consecutive_failures = 0


if __name__ == "__main__":
    autonomous_loop()