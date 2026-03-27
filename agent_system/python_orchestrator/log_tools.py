def _to_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)

def summarize_process_output(stdout, stderr) -> str:
    stdout = _to_text(stdout)
    stderr = _to_text(stderr)

    parts = []

    if stdout.strip():
        parts.append("STDOUT:\n" + stdout.strip())

    if stderr.strip():
        parts.append("STDERR:\n" + stderr.strip())

    if not parts:
        return "No output captured."

    return "\n\n".join(parts)