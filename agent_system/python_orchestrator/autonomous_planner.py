import json
from pathlib import Path
from datetime import datetime
from .model_client import call_model
from .config import ROOT, SHARED_DIR, LOGS_DIR, REVIEW_PROVIDER, REVIEW_API_KEY, REVIEW_MODEL_NAME
from typing import Optional  # add this import at the top

REGISTRY_FILE = SHARED_DIR / "capability_registry.json"
ACTIVE_ISSUE_FILE = SHARED_DIR / "active_issue.md"
ALERT_LOG_FILE = SHARED_DIR / "alert_log.md"

EDITABLE_FILES = [
    "bots/capabilities/movement.js",
    "bots/capabilities/gather.js",
    "bots/capabilities/build.js",
    "bots/capabilities/combat.js",
    "bots/agents/tim.js",
    "bots/planners/rule_planner.js",
]

def load_registry() -> dict:
    if not REGISTRY_FILE.exists():
        return {"capabilities": [], "roadmap": []}
    return json.loads(REGISTRY_FILE.read_text())

def save_registry(registry: dict):
    REGISTRY_FILE.write_text(json.dumps(registry, indent=2))

def get_stable_capability_ids(registry: dict) -> list[str]:
    return [c["id"] for c in registry["capabilities"] if c["status"] == "stable"]

def pick_next_capability(registry: dict) -> Optional[str]:
    stable = get_stable_capability_ids(registry)
    for item in registry.get("roadmap", []):
        if item not in stable:
            return item
    return None

def get_recent_logs(lines: int = 80) -> str:
    try:
        log_file = LOGS_DIR / "tim.log"
        all_lines = log_file.read_text().splitlines()
        return "\n".join(all_lines[-lines:])
    except Exception:
        return ""

def mark_capability_stable(registry: dict, capability_id: str, description: str) -> dict:
    for cap in registry["capabilities"]:
        if cap["id"] == capability_id:
            cap["status"] = "stable"
            return registry

    registry["capabilities"].append({
        "id": capability_id,
        "status": "stable",
        "added": datetime.now().strftime("%Y-%m-%d"),
        "description": description,
    })
    return registry

def write_alert(message: str):
    timestamp = datetime.now().isoformat()
    entry = f"\n## {timestamp}\n{message}\n"
    with open(ALERT_LOG_FILE, "a") as f:
        f.write(entry)
    print(f"\n🚨 ALERT: {message}\n")

def generate_issue_for_capability(capability_id: str, registry: dict) -> str:
    stable = get_stable_capability_ids(registry)
    recent_logs = get_recent_logs()

    system_prompt = """You are an autonomous Minecraft bot developer.
Your job is to write a focused development issue to add a new capability to a bot named Tim.
Tim is a Mineflayer bot running on a PaperMC 1.21.11 server.

Output ONLY the issue in this exact format with no preamble:

Issue: <one line description>

Success criteria:
- <criterion 1>
- <criterion 2>
- <criterion 3>

Editable files:
- <file 1>
- <file 2>

Max attempts:
- 5

Runtime seconds:
- 180

Rules:
- Success criteria must be observable in Tim's log output
- Keep changes incremental — build on existing capabilities
- Do not redesign the architecture
- Focus on one capability at a time"""

    user_prompt = f"""Tim currently has these stable capabilities: {stable}

Next capability to implement: {capability_id}

Tim's recent logs:
{recent_logs}

Available editable files:
{chr(10).join(f"- {f}" for f in EDITABLE_FILES)}

Write the development issue now."""

    return call_model(
        system_prompt,
        user_prompt,
        model_name=REVIEW_MODEL_NAME,
        provider=REVIEW_PROVIDER,
    )

def write_active_issue(issue_text: str):
    ACTIVE_ISSUE_FILE.write_text(issue_text)

def get_current_issue_title() -> str:
    try:
        content = ACTIVE_ISSUE_FILE.read_text()
        for line in content.splitlines():
            if line.startswith("Issue:"):
                return line.replace("Issue:", "").strip()
    except Exception:
        pass
    return ""