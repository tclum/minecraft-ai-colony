import json
from .config import ACTIVE_ISSUE_FILE, EDIT_PERMISSIONS_FILE
from .file_tools import read_text_file


def load_active_issue():
    raw = read_text_file(ACTIVE_ISSUE_FILE)

    issue = {
        "title": "",
        "success_criteria": [],
        "editable_files": [],
        "max_attempts": 3,
        "runtime_seconds": 120,
    }

    current_section = None

    for line in raw.splitlines():
        stripped = line.strip()

        if not stripped:
            continue

        if stripped.startswith("Issue:"):
            issue["title"] = stripped.replace("Issue:", "", 1).strip()
            current_section = None

        elif stripped.startswith("Max attempts:"):
            value = stripped.replace("Max attempts:", "", 1).strip()
            if value:
                try:
                    issue["max_attempts"] = int(value)
                except ValueError:
                    pass
                current_section = None
            else:
                current_section = "attempts"

        elif stripped.startswith("Runtime seconds:"):
            value = stripped.replace("Runtime seconds:", "", 1).strip()
            if value:
                try:
                    issue["runtime_seconds"] = int(value)
                except ValueError:
                    pass
                current_section = None
            else:
                current_section = "runtime"

        elif stripped == "Success criteria:":
            current_section = "success"

        elif stripped == "Editable files:":
            current_section = "files"

        elif stripped.startswith("- "):
            value = stripped[2:].strip()

            if current_section == "success":
                issue["success_criteria"].append(value)
            elif current_section == "files":
                issue["editable_files"].append(value)
            elif current_section == "attempts":
                try:
                    issue["max_attempts"] = int(value)
                except ValueError:
                    pass
            elif current_section == "runtime":
                try:
                    issue["runtime_seconds"] = int(value)
                except ValueError:
                    pass

    return issue


def load_edit_permissions():
    raw = read_text_file(EDIT_PERMISSIONS_FILE).strip()
    if not raw:
        return {"auto_edit_allowed": []}
    return json.loads(raw)