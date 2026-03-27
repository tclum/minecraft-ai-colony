from pathlib import Path
from .config import CURRENT_GOAL_FILE, PROJECT_SUMMARY_FILE, KNOWN_ISSUES_FILE, REPORT_FILE, ROOT
from .file_tools import read_text_file

KEY_SOURCE_FILES = [
    ROOT / "bots" / "agents" / "tim.js",
    ROOT / "bots" / "capabilities" / "gather.js",
    ROOT / "bots" / "capabilities" / "movement.js",
    # ROOT / "bots" / "planners" / "rule_planner.js",
    # ROOT / "bots" / "core" / "memory.js",
    # ROOT / "bots" / "core" / "logger.js",
]

def load_context():
    return {
        "current_goal": read_text_file(CURRENT_GOAL_FILE),
        "project_summary": read_text_file(PROJECT_SUMMARY_FILE),
        "known_issues": read_text_file(KNOWN_ISSUES_FILE),
        "last_report": read_text_file(REPORT_FILE),
    }

def load_key_source_files():
    files = {}
    for path in KEY_SOURCE_FILES:
        rel = path.relative_to(ROOT)
        files[str(rel)] = read_text_file(path)
    return files

def load_selected_source_files(relative_paths: list[str]):
    files = {}
    for rel_path in relative_paths:
        path = ROOT / rel_path
        files[rel_path] = read_text_file(path)
    return files