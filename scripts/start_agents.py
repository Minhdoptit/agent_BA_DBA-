#!/usr/bin/env python
"""scripts/start_agents.py - Process manager to start and monitor BA and DBA agents concurrently.

Starts:
- BA Agent on http://0.0.0.0:8003
- DBA Agent on http://0.0.0.0:8004
Verifies /health probe for readiness, streams logs, and ensures graceful termination.
"""

from __future__ import annotations

import argparse
import io
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

# Setup console encoding with instant line buffering for Windows
def _setup_console_encoding() -> None:
    if sys.platform == "win32" and hasattr(sys.stdout, "buffer"):
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)
        except Exception:
            pass

_setup_console_encoding()

try:
    import yaml
except ImportError:
    yaml = None

import httpx

ROOT_DIR = Path(__file__).resolve().parent.parent


def free_port(port: int) -> None:
    """Kills any previous leftover process holding the target port."""
    if sys.platform == "win32":
        try:
            cmd = f'powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess"'
            pids = subprocess.check_output(cmd, shell=True, text=True, errors="ignore").strip().splitlines()
            for pid_str in set(pids):
                pid_str = pid_str.strip()
                if pid_str.isdigit() and int(pid_str) != os.getpid():
                    print(f"[*] Releasing port {port} from old process PID {pid_str}...", flush=True)
                    os.system(f"taskkill /F /PID {pid_str} >nul 2>&1")
        except Exception:
            pass


def load_config() -> dict:
    """Loads configuration from config/agents.yaml with sensible defaults."""
    config_file = ROOT_DIR / "config" / "agents.yaml"
    if config_file.is_file() and yaml:
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as exc:
            print(f"[WARN] Failed to read agents.yaml: {exc}. Using fallback defaults.", flush=True)

    return {
        "agents": {
            "ba": {
                "id": "ba-01",
                "host": "0.0.0.0",
                "port": 8003,
                "api_key": "ba-secret-token-key-2026-secure-32chars",
            },
            "dba": {
                "id": "dba-01",
                "host": "0.0.0.0",
                "port": 8004,
                "api_key": "dba-secret-token-key-2026-secure-32chars",
            },
        }
    }


def wait_for_agent_healthy(url: str, timeout: float = 15.0) -> bool:
    """Polls agent /health endpoint until it responds with HTTP 200."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with httpx.Client(timeout=1.5) as client:
                res = client.get(f"{url}/health")
                if res.status_code == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def start_agent_process(
    agent_key: str,
    agent_cfg: dict,
    other_cfg: dict,
) -> subprocess.Popen:
    """Spawns an agent Uvicorn process with configured environment variables."""
    host = agent_cfg.get("host", "0.0.0.0")
    port = int(agent_cfg.get("port", 8003 if agent_key == "ba" else 8004))
    api_key = agent_cfg.get("api_key", "")

    # Ensure port is completely free
    free_port(port)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT_DIR)
    env["HOST"] = host
    env["PORT"] = str(port)
    env["AGENT_ID"] = agent_cfg.get("id", f"{agent_key}-01")
    env["AGENT_ROLE"] = agent_key.upper()
    env["AGENT_API_KEY"] = api_key
    env["ARTIFACT_DIR"] = str(ROOT_DIR / "agents" / agent_key / "artifacts")
    env["WORKSPACE_DIR"] = str(ROOT_DIR / "agents" / agent_key / "workspace")
    env["LOGS_DIR"] = str(ROOT_DIR / "agents" / agent_key / "logs")

    other_port = other_cfg.get("port", 8004 if agent_key == "ba" else 8003)
    other_key = other_cfg.get("api_key", "")
    if agent_key == "ba":
        env["DBA_ENDPOINT"] = f"http://127.0.0.1:{other_port}"
        env["DBA_API_KEY"] = other_key
    else:
        env["BA_ENDPOINT"] = f"http://127.0.0.1:{other_port}"
        env["BA_API_KEY"] = other_key

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        f"agents.{agent_key}.api:app",
        "--host",
        host,
        "--port",
        str(port),
        "--log-level",
        "info",
    ]

    print(f"[*] Starting {agent_key.upper()} Agent on http://{host}:{port} ...", flush=True)
    proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT_DIR),
        env=env,
        stdout=None,  # Output logs directly to console in real-time
        stderr=None,
    )
    return proc


def main():
    parser = argparse.ArgumentParser(description="Multi-Agent BA & DBA Launcher")
    parser.add_argument("--ba-only", action="store_true", help="Launch only BA Agent")
    parser.add_argument("--dba-only", action="store_true", help="Launch only DBA Agent")
    parser.add_argument("--timeout", type=float, default=15.0, help="Startup health check timeout in seconds")
    args = parser.parse_args()

    cfg = load_config()
    agents_cfg = cfg.get("agents", {})
    ba_cfg = agents_cfg.get("ba", {"port": 8003, "host": "0.0.0.0"})
    dba_cfg = agents_cfg.get("dba", {"port": 8004, "host": "0.0.0.0"})

    processes: Dict[str, subprocess.Popen] = {}

    def terminate_all():
        print("\n[*] Terminating all running agent processes...", flush=True)
        for name, p in processes.items():
            try:
                p.terminate()
                p.wait(timeout=2)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass
        print("[OK] All agents stopped.", flush=True)

    # Register signal handlers
    signal.signal(signal.SIGINT, lambda s, f: (terminate_all(), sys.exit(0)))
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, lambda s, f: (terminate_all(), sys.exit(0)))

    try:
        if not args.dba_only:
            proc_ba = start_agent_process("ba", ba_cfg, dba_cfg)
            processes["ba"] = proc_ba

        if not args.ba_only:
            proc_dba = start_agent_process("dba", dba_cfg, ba_cfg)
            processes["dba"] = proc_dba

        print("\n[*] Waiting for agent health probes...", flush=True)

        # Verify BA Health
        if "ba" in processes:
            ba_port = ba_cfg.get("port", 8003)
            if wait_for_agent_healthy(f"http://127.0.0.1:{ba_port}", timeout=args.timeout):
                print(f"  [OK] BA Agent is UP and HEALTHY at http://127.0.0.1:{ba_port} (PID: {processes['ba'].pid})", flush=True)
            else:
                print(f"  [FAIL] BA Agent failed to become healthy within {args.timeout}s", flush=True)

        # Verify DBA Health
        if "dba" in processes:
            dba_port = dba_cfg.get("port", 8004)
            if wait_for_agent_healthy(f"http://127.0.0.1:{dba_port}", timeout=args.timeout):
                print(f"  [OK] DBA Agent is UP and HEALTHY at http://127.0.0.1:{dba_port} (PID: {processes['dba'].pid})", flush=True)
            else:
                print(f"  [FAIL] DBA Agent failed to become healthy within {args.timeout}s", flush=True)

        print("\n" + "=" * 65, flush=True)
        print(" MULTI-AGENT BA & DBA SYSTEM RUNNING", flush=True)
        print("=" * 65, flush=True)
        print(f" - BA Agent:  http://127.0.0.1:{ba_cfg.get('port', 8003)}/health", flush=True)
        print(f" - DBA Agent: http://127.0.0.1:{dba_cfg.get('port', 8004)}/health", flush=True)
        print(" Press Ctrl+C to stop all agents.\n", flush=True)

        # Monitor loop
        while True:
            for name, p in list(processes.items()):
                ret = p.poll()
                if ret is not None:
                    print(f"[!] Process {name.upper()} exited unexpectedly with code {ret}", flush=True)
                    terminate_all()
                    return ret
            time.sleep(1)

    except KeyboardInterrupt:
        terminate_all()
    except Exception as exc:
        print(f"[!] Unexpected error: {exc}", flush=True)
        terminate_all()
        raise


if __name__ == "__main__":
    main()
