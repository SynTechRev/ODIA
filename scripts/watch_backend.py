"""watch_backend.py — ODIA backend watchdog.

Monitors port 18741 every 30 seconds. If the backend goes offline,
restarts it automatically and sends a Windows balloon-tip notification.

Run this in a SEPARATE terminal BEFORE starting any long ingest.
Leave it running for the full duration of the ingest.

Usage:
    .venv\\Scripts\\python scripts\\watch_backend.py
    .venv\\Scripts\\python scripts\\watch_backend.py --port 8000
    .venv\\Scripts\\python scripts\\watch_backend.py --check-interval 15
"""

from __future__ import annotations

import argparse
import http.client
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_PORT = 18741
DEFAULT_CHECK_INTERVAL = 30  # seconds


def _ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _backend_alive(port: int) -> bool:
    try:
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        conn.request("GET", "/health")
        r = conn.getresponse()
        r.read()
        return r.status < 500
    except Exception:
        return False


def _notify(title: str, message: str) -> None:
    """Windows balloon-tip notification. Best-effort, never raises."""
    try:
        ps = (
            "Add-Type -AssemblyName System.Windows.Forms; "
            "$n = New-Object System.Windows.Forms.NotifyIcon; "
            "$n.Icon = [System.Drawing.SystemIcons]::Warning; "
            "$n.Visible = $true; "
            f'$n.ShowBalloonTip(20000, "{title}", "{message}", '
            "[System.Windows.Forms.ToolTipIcon]::Warning); "
            "Start-Sleep -Seconds 20; $n.Dispose()"
        )
        subprocess.Popen(
            ["powershell", "-WindowStyle", "Hidden", "-NonInteractive", "-Command", ps],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


def _start_backend(port: int, log_path: Path) -> subprocess.Popen:
    python = _REPO_ROOT / ".venv" / "Scripts" / "python.exe"
    if not python.exists():
        python = _REPO_ROOT / ".venv" / "bin" / "python"
    cmd = [
        str(python),
        "-m",
        "uvicorn",
        "oraculus_di_auditor.interface.api:app",
        "--port",
        str(port),
        "--no-access-log",
    ]
    print(f"[{_ts()}] Launching: {' '.join(cmd)}")
    log_fh = open(log_path, "a", encoding="utf-8")
    log_fh.write(f"\n--- watchdog restart at {_ts()} ---\n")
    log_fh.flush()
    proc = subprocess.Popen(
        cmd,
        cwd=str(_REPO_ROOT),
        stdout=log_fh,
        stderr=subprocess.STDOUT,
    )
    return proc


def main() -> None:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

    parser = argparse.ArgumentParser(description="ODIA backend watchdog")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--check-interval",
        type=int,
        default=DEFAULT_CHECK_INTERVAL,
        help="Seconds between health checks (default: 30)",
    )
    args = parser.parse_args()

    port = args.port
    interval = args.check_interval

    logs_dir = _REPO_ROOT / "logs"
    logs_dir.mkdir(exist_ok=True)
    backend_log = logs_dir / "backend.log"

    print("ODIA Backend Watchdog")
    print(f"  Port:           {port}")
    print(f"  Check interval: {interval}s")
    print(f"  Backend log:    {backend_log}")
    print("  Ctrl+C to stop\n")

    backend_proc: subprocess.Popen | None = None
    restarts = 0

    # Initial state
    if not _backend_alive(port):
        print(f"[{_ts()}] Backend not running — starting...")
        backend_proc = _start_backend(port, backend_log)
        # Wait up to 15s for startup
        for _ in range(3):
            time.sleep(5)
            if _backend_alive(port):
                break
        if _backend_alive(port):
            print(f"[{_ts()}] Backend started OK (PID {backend_proc.pid})")
            _notify("ODIA Watchdog", f"Backend started on port {port}.")
        else:
            print(
                f"[{_ts()}] Backend started but not yet responding — continuing to monitor"
            )
    else:
        print(f"[{_ts()}] Backend already running on port {port} — monitoring")

    # Monitor loop
    while True:
        time.sleep(interval)

        if _backend_alive(port):
            # Quiet tick — overwrite the same line
            print(f"[{_ts()}] OK :{port}", end="\r", flush=True)
            # If our managed process exited cleanly, clear the reference
            if backend_proc is not None and backend_proc.poll() is not None:
                backend_proc = None
            continue

        # Backend is down
        restarts += 1
        print(f"\n[{_ts()}] BACKEND DOWN — restart #{restarts}")
        _notify(
            "ODIA Backend Restarted",
            f"Backend went offline and was restarted (#{restarts}). Ingest will resume automatically.",
        )

        # Terminate stale managed process if we own it
        if backend_proc is not None and backend_proc.poll() is None:
            try:
                backend_proc.terminate()
            except Exception:
                pass

        backend_proc = _start_backend(port, backend_log)
        print(f"[{_ts()}] Waiting for backend to come up (PID {backend_proc.pid})...")

        # Wait up to 60s for it to respond
        came_up = False
        for _ in range(12):
            time.sleep(5)
            if _backend_alive(port):
                came_up = True
                break

        if came_up:
            print(
                f"[{_ts()}] Backend back online (PID {backend_proc.pid}) after restart #{restarts}"
            )
            _notify(
                "ODIA Backend Online",
                f"Backend is back on port {port}. Ingest will continue.",
            )
        else:
            print(
                f"[{_ts()}] ERROR: Backend failed to come back after 60s. Check {backend_log}"
            )
            _notify(
                "ODIA Backend FAILED",
                "Backend could not restart after 60s. Manual intervention needed. See logs/backend.log",
            )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nWatchdog stopped.")
