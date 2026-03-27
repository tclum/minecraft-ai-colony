import subprocess
from .config import ROOT, START_TIM_COMMAND

def _to_text(value):
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)

def run_tim(timeout_seconds: int = 150):
    try:
        result = subprocess.run(
            START_TIM_COMMAND,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": _to_text(result.stdout),
            "stderr": _to_text(result.stderr)
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "success": True,
            "returncode": None,
            "stdout": _to_text(exc.stdout),
            "stderr": _to_text(exc.stderr) + f"\n[runner] Tim process timed out after {timeout_seconds}s (treated as expected for long-running bot)."
        }
    except Exception as exc:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": f"[runner] Exception: {exc}"
        }