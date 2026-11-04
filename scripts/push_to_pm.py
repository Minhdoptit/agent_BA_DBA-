"""scripts/push_to_pm.py - CLI tool to push all BA and DBA artifacts to the PM Agent.

Usage:
    python scripts/push_to_pm.py [--pm-url http://<IP>:8001] [--pm-token <TOKEN>] [--target all|ba|dba]
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

# Ensure console supports utf-8 output on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "buffer"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent


def load_config_defaults() -> tuple[str, str]:
    """Read default PM endpoint and token from agents.yaml or env files."""
    pm_endpoint = os.getenv("PM_ENDPOINT", "")
    pm_token = os.getenv("PM_API_KEY", "") or os.getenv("AGENT_API_KEY_PM_01", "")

    # Try config/agents.yaml
    yaml_file = ROOT_DIR / "config" / "agents.yaml"
    if yaml_file.is_file():
        try:
            import yaml
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                pm_sec = data.get("agents", {}).get("pm", {})
                if not pm_endpoint and pm_sec.get("endpoint"):
                    pm_endpoint = str(pm_sec.get("endpoint"))
                if not pm_token and pm_sec.get("api_key"):
                    pm_token = str(pm_sec.get("api_key"))
        except Exception:
            pass

    # Try BA or DBA .env
    for env_path in [ROOT_DIR / "agents" / "ba" / ".env", ROOT_DIR / "agents" / "dba" / ".env", ROOT_DIR / ".env.lan"]:
        if env_path.is_file():
            try:
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line.startswith("PM_ENDPOINT=") and not pm_endpoint:
                        pm_endpoint = line.split("=", 1)[1].strip()
                    elif line.startswith("PM_API_KEY=") and not pm_token:
                        pm_token = line.split("=", 1)[1].strip()
                    elif line.startswith("AGENT_API_KEY_PM_01=") and not pm_token:
                        pm_token = line.split("=", 1)[1].strip()
            except Exception:
                pass

    if not pm_endpoint:
        pm_endpoint = "http://127.0.0.1:8001"

    return pm_endpoint.rstrip("/"), pm_token


def push_file_to_inbox(
    client: httpx.Client,
    inbox_url: str,
    headers: Dict[str, str],
    file_path: Path,
    agent_id: str,
    artifact_type: str,
) -> Dict[str, Any]:
    """Upload a single file to PM inbox."""
    filename = file_path.name
    raw_bytes = file_path.read_bytes()

    if file_path.suffix.lower() == ".docx":
        content_str = base64.b64encode(raw_bytes).decode("utf-8")
    else:
        content_str = file_path.read_text(encoding="utf-8")

    checksum = hashlib.sha256(content_str.encode("utf-8")).hexdigest()

    payload = {
        "artifact_id": filename,
        "filename": filename,
        "type": artifact_type,
        "artifact_type": artifact_type,
        "created_by": agent_id,
        "source_agent": agent_id,
        "content": content_str,
        "checksum": checksum,
    }

    try:
        resp = client.post(inbox_url, json=payload, headers=headers)
        return {
            "file": filename,
            "agent": agent_id,
            "status_code": resp.status_code,
            "ok": resp.status_code in (200, 201),
            "size": len(raw_bytes),
            "checksum": checksum[:8],
            "response": resp.text[:120],
        }
    except Exception as exc:
        return {
            "file": filename,
            "agent": agent_id,
            "status_code": 0,
            "ok": False,
            "size": len(raw_bytes),
            "checksum": checksum[:8],
            "error": str(exc),
        }


def main():
    default_url, default_token = load_config_defaults()

    parser = argparse.ArgumentParser(description="Push BA and DBA artifacts to PM Agent")
    parser.add_argument("--pm-url", default=default_url, help=f"PM Agent Endpoint URL (default: {default_url})")
    parser.add_argument("--pm-token", default=default_token, help="PM Agent Bearer Token (optional)")
    parser.add_argument("--target", choices=["all", "ba", "dba"], default="all", help="Which agent artifacts to push")
    parser.add_argument("--file", help="Push a specific file name only")
    args = parser.parse_args()

    pm_endpoint = args.pm_url.rstrip("/")
    pm_token = args.pm_token
    inbox_url = f"{pm_endpoint}/artifacts/inbox"

    headers = {"Content-Type": "application/json"}
    if pm_token:
        headers["Authorization"] = f"Bearer {pm_token}"

    print("=" * 80)
    print(f"[*] ARTIFACT DISPATCHER -> PM AGENT (pm-01)")
    print(f"[*] PM Endpoint:  {pm_endpoint}")
    print(f"[*] Inbox URL:    {inbox_url}")
    print(f"[*] Token Auth:   {'[YES - Protected]' if pm_token else '[NO - Public/None]'}")
    print("=" * 80)

    ba_dir = ROOT_DIR / "agents" / "ba" / "artifacts"
    dba_dir = ROOT_DIR / "agents" / "dba" / "artifacts"

    items_to_push: List[tuple[Path, str, str]] = []

    # BA Artifact types
    ba_types = {
        "SRS.md": "SRS_DOCUMENT",
        "srs.docs": "SRS_DOCUMENT",
        "SRS.docx": "SRS_DOCUMENT",
        "REQUIREMENTS.md": "REQUIREMENTS_SPEC",
        "USER_STORIES.md": "USER_STORIES",
        "USE_CASES.md": "USE_CASES",
        "ACCEPTANCE_CRITERIA.md": "ACCEPTANCE_CRITERIA",
        "BUSINESS_PROCESS.md": "BUSINESS_PROCESS",
    }

    # DBA Artifact types
    dba_types = {
        "schema.sql": "DATABASE_SCHEMA",
        "ERD.md": "ERD_DIAGRAM",
        "DATABASE_DESIGN.md": "DATABASE_DESIGN",
        "DATA_REQUIREMENTS.md": "DATA_REQUIREMENTS",
        "INDEX_STRATEGY.md": "INDEX_STRATEGY",
        "DATABASE_REVIEW.md": "DATABASE_REVIEW",
    }

    if args.target in ("all", "ba") and ba_dir.is_dir():
        for ext in ["*.md", "*.docs", "*.docx"]:
            for f in sorted(ba_dir.glob(ext)):
                if not f.name.startswith("~$"):
                    if not args.file or f.name == args.file:
                        items_to_push.append((f, "ba-01", ba_types.get(f.name, "SPECIFICATION")))

    if args.target in ("all", "dba") and dba_dir.is_dir():
        for ext in ["*.sql", "*.md"]:
            for f in sorted(dba_dir.glob(ext)):
                if not f.name.startswith("~$") and "inbox" not in str(f):
                    if not args.file or f.name == args.file:
                        items_to_push.append((f, "dba-01", dba_types.get(f.name, "DATABASE_SPECIFICATION")))

    if not items_to_push:
        print("[!] No artifacts found to push.")
        sys.exit(0)

    print(f"[*] Found {len(items_to_push)} artifacts ready for delivery.")
    print("-" * 80)

    success_count = 0
    fail_count = 0

    with httpx.Client(timeout=15.0) as client:
        # Step 1: Probe PM health
        try:
            h_resp = client.get(f"{pm_endpoint}/health")
            if h_resp.status_code == 200:
                print(f"[OK] PM Agent is reachable at {pm_endpoint}/health")
            else:
                print(f"[?] PM Agent returned HTTP {h_resp.status_code} at /health")
        except Exception as exc:
            print(f"[WARNING] Cannot connect to PM Agent /health ({exc}). Attempting inbox push anyway...")

        print("-" * 80)

        for file_path, agent_id, art_type in items_to_push:
            res = push_file_to_inbox(client, inbox_url, headers, file_path, agent_id, art_type)
            if res["ok"]:
                success_count += 1
                status_str = f"\033[92m[PASS {res['status_code']}]\033[0m" if sys.platform != "win32" else f"[PASS {res['status_code']}]"
                print(f"[{agent_id:6}] {res['file']:25} -> {status_str} ({res['size']}B, SHA: {res['checksum']})")
            else:
                fail_count += 1
                err_msg = res.get("error") or res.get("response") or "Unknown"
                status_str = f"[FAIL {res['status_code']}]"
                print(f"[{agent_id:6}] {res['file']:25} -> {status_str} Error: {err_msg[:60]}")

    print("=" * 80)
    print(f"[*] DELIVERY SUMMARY: Total: {len(items_to_push)} | Success: {success_count} | Failed: {fail_count}")
    if fail_count > 0:
        print("[!] TIP: Make sure the PM Agent on Machine 1 is running and listening on port 8001.")
        print(f"[!] Target URL tested: {inbox_url}")
    print("=" * 80)


if __name__ == "__main__":
    main()
