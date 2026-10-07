"""watch_backend.py — ODIA backend watchdog.

Monitors port 18741 every 30 seconds. If the backend goes offline,
restarts it automatically and sends a Windows balloon-tip notification.

Run this in a SEPARATE terminal BEFORE starting any long ingest.
Leave it running for the full duration of the ingest.

Usage:
    .venv\\Scripts\\python scripts\\watch_backend.py
    .venv\\Scripts\\python scripts\\watch_backend.py --port 8000
    .venv\\Scripts\\python scripts\\watch_backend.py --check-interval 15

Liveness model
--------------
TCP socket check is the primary liveness signal.  A TCP connect succeeds
as long as *something* is bound to the port — even when the backend is
busy processing a large PDF and can't respond to HTTP within the usual
5-second window.  Three consecutive TCP failures (90 s at the default
30-second interval) are required before the watchdog concludes the
backend is truly dead and issues a restart.

Before spawning a new process the watchdog kills any process still
holding the port via Get-NetTCPConnection / Stop-Process, preventing the
WinError 10048 "address already in use" crash loop.
"""

from __future__ import annotations

import argparse
import http.client
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_PORT = 18741
DEFAULT_CHECK_INTERVAL = 30  # seconds
FAIL_THRESHOLD = 3  # consecutive TCP failures before restart


def _ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _port_is_open(port: int) -> bool:
    """TCP-level liveness check: is anything listening on the port?

    Returns True even when the backend is busy and HTTP would time out.
    This is the primary signal used by the monitor loop.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        result = s.connect_ex(("127.0.0.1", port))
        s.close()
        return result == 0
    except Exception:
        return False


def _http_alive(port: int, timeout: int = 20) -> bool:
    """HTTP health check — used only to confirm a fresh process came up."""
    try:
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
        conn.request("GET", "/health")
        r = conn.getresponse()
        r.read()
        return r.status < 500
    except Exception:
        return False


def _get_mem_mb(pid: int) -> float | None:
    """Return process WorkingSet in MB. Best-effort; returns None on failure."""
    try:
        import psutil

        return psutil.Process(pid).memory_info().rss / (1024 * 1024)
    except Exception:
        pass
    try:
        r = subprocess.run(
            [
                "powershell",
                "-NonInteractive",
                "-Command",
                f"$p = Get-Process -Id {pid} -ErrorAction SilentlyContinue; "
                f"if ($p) {{ [math]::Round($p.WorkingSet / 1MB, 1) }}",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        val = r.stdout.strip()
        if val:
            return float(val)
    except Exception:
        pass
    return None


def _set_below_normal_priority(pid: int) -> None:
    """Lower the process to BELOW_NORMAL CPU priority. Best-effort."""
    try:
        subprocess.run(
            [
                "powershell",
                "-NonInteractive",
                "-Command",
                f"(Get-Process -Id {pid} -ErrorAction SilentlyContinue)"
                f".PriorityClass = 'BelowNormal'",
            ],
            capture_output=True,
            timeout=5,
        )
    except Exception:
        pass


def _kill_port(port: int) -> None:
    """Kill any process currently bound to *port*.  Best-effort, never raises.

    Prevents WinError 10048 when the old process hasn't released the port
    before the watchdog spawns a new one.
    """
    try:
        subprocess.run(
            [
                "powershell",
                "-NonInteractive",
                "-Command",
                (
                    f"$c = Get-NetTCPConnection -LocalPort {port} -State Listen "
                    f"-ErrorAction SilentlyContinue; "
                    f"if ($c) {{ "
                    f"  Stop-Process -Id $c.OwningProcess -Force "
                    f"  -ErrorAction SilentlyContinue; "
                    f"  Start-Sleep -Milliseconds 1500 "
                    f"}}"
                ),
            ],
            timeout=8,
            capture_output=True,
        )
    except Exception:
        pass


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
    """Kill anything on the port, then spawn a fresh uvicorn process."""
    _kill_port(port)

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

    mem_restart_mb = 1500  # restart backend if WorkingSet exceeds this

    print("ODIA Backend Watchdog")
    print(f"  Port:              {port}")
    print(f"  Check interval:    {interval}s")
    print(
        f"  Fail threshold:    {FAIL_THRESHOLD} consecutive misses (~{FAIL_THRESHOLD * interval}s)"
    )
    print(f"  Memory ceiling:    {mem_restart_mb} MB")
    print(f"  Backend log:       {backend_log}")
    print("  Ctrl+C to stop\n")
    print(
        "  Liveness: TCP socket (succeeds even when backend is busy with large PDFs)\n"
    )

    backend_proc: subprocess.Popen | None = None
    backend_pid: int | None = None  # PID of the live backend (owned or adopted)
    restarts = 0
    consecutive_failures = 0

    def _adopt_port_pid() -> int | None:
        """Return the PID of whatever process currently holds the port."""
        try:
            r = subprocess.run(
                [
                    "powershell",
                    "-NonInteractive",
                    "-Command",
                    f"(Get-NetTCPConnection -LocalPort {port} -State Listen "
                    f"-ErrorAction SilentlyContinue).OwningProcess",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            val = r.stdout.strip()
            return int(val) if val else None
        except Exception:
            return None

    # Initial state — adopt a running backend, or start one
    if not _port_is_open(port):
        print(f"[{_ts()}] Backend not running — starting...")
        backend_proc = _start_backend(port, backend_log)
        backend_pid = backend_proc.pid
        _set_below_normal_priority(backend_pid)
        # Wait up to 30s for startup
        for _ in range(6):
            time.sleep(5)
            if _port_is_open(port):
                break
        if _port_is_open(port):
            print(f"[{_ts()}] Backend started OK (PID {backend_pid})")
            _notify("ODIA Watchdog", f"Backend started on port {port}.")
        else:
            print(
                f"[{_ts()}] Backend started but not yet responding — continuing to monitor"
            )
    else:
        backend_pid = _adopt_port_pid()
        if backend_pid:
            _set_below_normal_priority(backend_pid)
        print(
            f"[{_ts()}] Backend already running on port {port} "
            f"(PID {backend_pid}) — adopting (no restart)"
        )
        _notify("ODIA Watchdog", f"Monitoring backend on port {port}.")

    # Monitor loop
    while True:
        time.sleep(interval)

        if _port_is_open(port):
            consecutive_failures = 0
            # Clear stale reference if our process exited (backend was restarted externally)
            if backend_proc is not None and backend_proc.poll() is not None:
                backend_proc = None
                backend_pid = _adopt_port_pid()

            # Memory guard: if the backend is leaking, restart before OOM.
            if backend_pid is not None:
                mem = _get_mem_mb(backend_pid)
                if mem is not None and mem > mem_restart_mb:
                    print(
                        f"\n[{_ts()}] MEMORY {mem:.0f} MB > {mem_restart_mb} MB ceiling — restarting",
                        flush=True,
                    )
                    _notify(
                        "ODIA Backend Memory Restart",
                        f"Backend at {mem:.0f} MB — restarting to reclaim RAM.",
                    )
                    if backend_proc is not None and backend_proc.poll() is None:
                        try:
                            backend_proc.terminate()
                        except Exception:
                            pass
                    restarts += 1
                    backend_proc = _start_backend(port, backend_log)
                    backend_pid = backend_proc.pid
                    _set_below_normal_priority(backend_pid)
                    print(
                        f"[{_ts()}] Backend restarted (PID {backend_pid}) — restart #{restarts}"
                    )
                    _notify("ODIA Backend Online", f"Backend restarted on port {port}.")
                    continue

            print(f"[{_ts()}] OK :{port}", end="\r", flush=True)
            continue

        # TCP connect failed
        consecutive_failures += 1
        remaining = FAIL_THRESHOLD - consecutive_failures
        if remaining > 0:
            print(
                f"\n[{_ts()}] TCP miss #{consecutive_failures}/{FAIL_THRESHOLD} "
                f"— waiting for {remaining} more before restart",
                flush=True,
            )
            continue

        # FAIL_THRESHOLD consecutive misses — truly dead
        consecutive_failures = 0
        restarts += 1
        print(f"\n[{_ts()}] BACKEND DOWN (confirmed) — restart #{restarts}")
        _notify(
            "ODIA Backend Restarted",
            f"Backend went offline (restart #{restarts}). Ingest will resume automatically.",
        )

        # Terminate any stale managed process
        if backend_proc is not None and backend_proc.poll() is None:
            try:
                backend_proc.terminate()
            except Exception:
                pass

        backend_proc = _start_backend(port, backend_log)
        backend_pid = backend_proc.pid
        _set_below_normal_priority(backend_pid)
        print(f"[{_ts()}] Waiting for backend to come up (PID {backend_pid})...")

        # Wait up to 60s for TCP to open
        came_up = False
        for _ in range(12):
            time.sleep(5)
            if _port_is_open(port):
                came_up = True
                break

        if came_up:
            print(
                f"[{_ts()}] Backend back online (PID {backend_pid}) — restart #{restarts}"
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
