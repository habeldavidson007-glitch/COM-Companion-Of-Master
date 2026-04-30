"""Signal harness dispatcher wired to real tool_harness."""

from tools.tool_harness import execute_signal


def dispatch(signal_output: str) -> str:
    signal = signal_output.strip()
    result = execute_signal(signal)
    if result.get("success"):
        payload = result.get("result", {})
        return payload.get("message", str(payload))
    return f"[ERROR] {result.get('error', 'unknown error')}"
