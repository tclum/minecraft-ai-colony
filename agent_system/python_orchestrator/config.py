from pathlib import Path
import os
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

SHARED_DIR = ROOT / "agent_system" / "shared"
LOGS_DIR = ROOT / "logs"
MEMORY_DIR = ROOT / "memory"

CURRENT_GOAL_FILE = SHARED_DIR / "current_goal.md"
PROJECT_SUMMARY_FILE = SHARED_DIR / "project_summary.md"
KNOWN_ISSUES_FILE = SHARED_DIR / "known_issues.md"
BACKLOG_FILE = SHARED_DIR / "backlog.json"
PERMISSIONS_FILE = SHARED_DIR / "permissions.json"
REPORT_FILE = SHARED_DIR / "last_report.md"
LLM_PLAN_FILE = SHARED_DIR / "llm_plan.md"
PROPOSED_PATCH_FILE = SHARED_DIR / "proposed_patch.md"
REVIEWED_ACTIONS_FILE = SHARED_DIR / "reviewed_actions.md"
NEXT_ACTIONS_FILE = SHARED_DIR / "next_actions.md"
PATCH_REVIEW_FILE = SHARED_DIR / "patch_review.json"

ACTIVE_ISSUE_FILE = SHARED_DIR / "active_issue.md"
EDIT_PERMISSIONS_FILE = SHARED_DIR / "edit_permissions.json"
ATTEMPT_HISTORY_FILE = SHARED_DIR / "attempt_history.md"
BACKUP_DIR = SHARED_DIR / "original_backups"

START_TIM_COMMAND = ["node", "agent_system/node_bridge/start_tim.js"]

MODEL_API_KEY = os.getenv("MODEL_API_KEY", "")
MODEL_BASE_URL = os.getenv("MODEL_BASE_URL", "")
MODEL_NAME = os.getenv("MODEL_NAME", "")

REVIEW_PROVIDER = os.getenv("REVIEW_PROVIDER", "openai")
REVIEW_API_KEY = os.getenv("REVIEW_API_KEY")
REVIEW_MODEL_NAME = os.getenv("REVIEW_MODEL_NAME", MODEL_NAME)
PATCH_REVIEW_FILE = SHARED_DIR / "patch_review.json"
