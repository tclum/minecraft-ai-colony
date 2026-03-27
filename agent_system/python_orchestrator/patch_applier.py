from .config import ROOT

def verify_patch_paths(patch_data: dict, allowed_files: list[str]) -> tuple[bool, list[str]]:
    patch_files = [item["path"] for item in patch_data.get("files", [])]
    disallowed = [p for p in patch_files if p not in allowed_files]
    return (len(disallowed) == 0, disallowed)

def apply_patch_files(patch_data: dict):
    for item in patch_data.get("files", []):
        path = ROOT / item["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(item["content"], encoding="utf-8")