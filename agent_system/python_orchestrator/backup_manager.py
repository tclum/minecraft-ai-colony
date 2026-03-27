from pathlib import Path
import shutil
from .config import ROOT, BACKUP_DIR

def backup_original_once(relative_file_path: str):
    source = ROOT / relative_file_path
    target = BACKUP_DIR / relative_file_path

    if not source.exists():
        raise FileNotFoundError(f"Cannot back up missing file: {relative_file_path}")

    if target.exists():
        return False

    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return True