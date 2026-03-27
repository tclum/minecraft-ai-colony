import json
from .config import BACKLOG_FILE, PERMISSIONS_FILE
from .file_tools import read_text_file

def load_backlog():
    raw = read_text_file(BACKLOG_FILE).strip()
    if not raw:
        return []
    return json.loads(raw)

def load_permissions():
    raw = read_text_file(PERMISSIONS_FILE).strip()
    if not raw:
        return {}
    return json.loads(raw)