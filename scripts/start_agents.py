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

# Setup console encoding for Windows compatibility
def _setup_console_encoding() -> None:
    if sys.platform == "win32" and hasattr(sys.stdout, "buffer"):
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
        except Exception:
            pass

_setup_console_encoding()

try:
    import yaml
except ImportError:
    yaml = None

import httpx

ROOT_DIR = Path(__file__).resolve().parent.parent


def load_config() -> dict:
    """Loads configuration from config/agents.yaml with sensible defaults."""
    config_file = ROOT_DIR / "config" / "agents.yaml"
    if config_file.is_file() and yaml:
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as exc:
            print(f"[WARN] Failed to read agents.yaml: {exc}. Using fallback defaults.")

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

    # Pass peer agent endpoint and key for cross-agent API communication
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

    print(f"[*] Starting {agent_key.upper()} Agent on http://{host}:{port} ...")
    proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
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
        print("\n[*] Terminating all running agent processes...")
        for name, p in processes.items():
            try:
                p.terminate()
                p.wait(timeout=3)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass
        print("[OK] All agents stopped.")

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

        print("\n[*] Waiting for agent health probes...")

        # Verify BA Health
        if "ba" in processes:
            ba_port = ba_cfg.get("port", 8003)
            if wait_for_agent_healthy(f"http://127.0.0.1:{ba_port}", timeout=args.timeout):
                print(f"  [OK] BA Agent is UP and HEALTHY at http://127.0.0.1:{ba_port} (PID: {processes['ba'].pid})")
            else:
                print(f"  [FAIL] BA Agent failed to become healthy within {args.timeout}s")

        # Verify DBA Health
        if "dba" in processes:
            dba_port = dba_cfg.get("port", 8004)
            if wait_for_agent_healthy(f"http://127.0.0.1:{dba_port}", timeout=args.timeout):
                print(f"  [OK] DBA Agent is UP and HEALTHY at http://127.0.0.1:{dba_port} (PID: {processes['dba'].pid})")
            else:
                print(f"  [FAIL] DBA Agent failed to become healthy within {args.timeout}s")

        print("\n" + "=" * 65)
        print(" MULTI-AGENT BA & DBA SYSTEM RUNNING")
        print("=" * 65)
        print(f" - BA Agent:  http://127.0.0.1:{ba_cfg.get('port', 8003)}/health")
        print(f" - DBA Agent: http://127.0.0.1:{dba_cfg.get('port', 8004)}/health")
        print(" Press Ctrl+C to stop all agents.\n")

        # Monitor loop
        while True:
            for name, p in list(processes.items()):
                ret = p.poll()
                if ret is not None:
                    print(f"[!] Process {name.upper()} exited unexpectedly with code {ret}")
                    if p.stdout:
                        out = p.stdout.read()
                        if out:
                            print(out)
                    terminate_all()
                    return ret
            time.sleep(1)

    except KeyboardInterrupt:
        terminate_all()
    except Exception as exc:
        print(f"[!] Unexpected error: {exc}")
        terminate_all()
        raise


if __name__ == "__main__":
    main()
