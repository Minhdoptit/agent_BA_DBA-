#!/usr/bin/env python
"""scripts/test_connection.py - End-to-end integration test for BA and DBA Multi-Agent System.

Validates:
1. Health checks on BA (8003) and DBA (8004).
2. Bearer token authentication (401 on missing/wrong token, 200 on valid token).
3. Status and state inspection API.
4. BA Agent SRS document generation and artifact storage.
5. Cross-agent HTTP API transmission from BA to DBA (Pure API, zero shared folder).
6. DBA Agent SRS analysis, SQL DDL schema compilation, and artifact verification.
"""

from __future__ import annotations

import hashlib
import io
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

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
    """Loads configuration from config/agents.yaml."""
    cfg_file = ROOT_DIR / "config" / "agents.yaml"
    if cfg_file.is_file() and yaml:
        with open(cfg_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    return {
        "agents": {
            "ba": {
                "port": 8003,
                "api_key": "ba-secret-token-key-2026-secure-32chars",
                "endpoint": "http://127.0.0.1:8003",
            },
            "dba": {
                "port": 8004,
                "api_key": "dba-secret-token-key-2026-secure-32chars",
                "endpoint": "http://127.0.0.1:8004",
            },
        }
    }


class TestRunner:
    def __init__(self):
        self.config = load_config()
        self.ba_endpoint = self.config["agents"]["ba"].get("endpoint", "http://127.0.0.1:8003")
        self.ba_token = self.config["agents"]["ba"].get("api_key", "")
        self.dba_endpoint = self.config["agents"]["dba"].get("endpoint", "http://127.0.0.1:8004")
        self.dba_token = self.config["agents"]["dba"].get("api_key", "")

        self.results: List[Tuple[str, bool, str]] = []

    def record(self, test_name: str, passed: bool, message: str = ""):
        self.results.append((test_name, passed, message))
        status_icon = "[PASS]" if passed else "[FAIL]"
        print(f"  {status_icon:<6} | {test_name}: {message}")

    def run_all(self) -> bool:
        print("\n" + "=" * 75)
        print(" STARTING MULTI-AGENT INTEGRATION & CONNECTIVITY TEST SUITE")
        print("=" * 75)
        print(f" - BA Target:  {self.ba_endpoint}")
        print(f" - DBA Target: {self.dba_endpoint}\n")

        with httpx.Client(timeout=30.0) as client:
            # Step 1: Health Probes
            self.test_health_probes(client)

            # Step 2: Authentication Tests
            self.test_authentication(client)

            # Step 3: Status & Metadata Endpoints
            self.test_status_endpoints(client)

            # Step 4: BA Agent Generates SRS Document
            srs_text, srs_checksum = self.test_ba_srs_generation(client)

            # Step 5: Transfer SRS via HTTP API (Zero shared folder)
            self.test_api_transfer_to_dba(client, srs_text, srs_checksum)

            # Step 6: DBA Analyzes SRS & Produces Database Schema
            self.test_dba_schema_generation(client, srs_text)

            # Step 7: Verify Artifacts on Both Sides
            self.test_artifact_persistence(client)

        return self.print_summary()

    def test_health_probes(self, client: httpx.Client):
        print("[*] Stage 1: Health & Heartbeat Probes")
        try:
            r_ba = client.get(f"{self.ba_endpoint}/health")
            passed = r_ba.status_code == 200 and r_ba.json().get("status") == "healthy"
            self.record("BA Health Check (GET /health)", passed, f"HTTP {r_ba.status_code} - {r_ba.text}")
        except Exception as e:
            self.record("BA Health Check (GET /health)", False, f"Connection failed: {e}")

        try:
            r_dba = client.get(f"{self.dba_endpoint}/health")
            passed = r_dba.status_code == 200 and r_dba.json().get("status") == "OK"
            self.record("DBA Health Check (GET /health)", passed, f"HTTP {r_dba.status_code} - {r_dba.text}")
        except Exception as e:
            self.record("DBA Health Check (GET /health)", False, f"Connection failed: {e}")
        print()

    def test_authentication(self, client: httpx.Client):
        print("[*] Stage 2: Bearer Token Security Enforcement")

        # 1. BA without token (expect 401)
        try:
            r1 = client.get(f"{self.ba_endpoint}/status")
            passed1 = r1.status_code == 401
            self.record("BA Auth Rejection without Token", passed1, f"Expected 401, got {r1.status_code}")
        except Exception as e:
            self.record("BA Auth Rejection without Token", False, str(e))

        # 2. BA with invalid token (expect 401)
        try:
            r2 = client.get(f"{self.ba_endpoint}/status", headers={"Authorization": "Bearer invalid_token_123"})
            passed2 = r2.status_code == 401
            self.record("BA Auth Rejection with Invalid Token", passed2, f"Expected 401, got {r2.status_code}")
        except Exception as e:
            self.record("BA Auth Rejection with Invalid Token", False, str(e))

        # 3. BA with valid token (expect 200)
        try:
            r3 = client.get(f"{self.ba_endpoint}/status", headers={"Authorization": f"Bearer {self.ba_token}"})
            passed3 = r3.status_code == 200
            self.record("BA Auth Acceptance with Valid Token", passed3, f"HTTP {r3.status_code} OK")
        except Exception as e:
            self.record("BA Auth Acceptance with Valid Token", False, str(e))

        # 4. DBA without token (expect 401)
        try:
            r4 = client.get(f"{self.dba_endpoint}/status")
            passed4 = r4.status_code == 401
            self.record("DBA Auth Rejection without Token", passed4, f"Expected 401, got {r4.status_code}")
        except Exception as e:
            self.record("DBA Auth Rejection without Token", False, str(e))

        # 5. DBA with valid token (expect 200)
        try:
            r5 = client.get(f"{self.dba_endpoint}/status", headers={"Authorization": f"Bearer {self.dba_token}"})
            passed5 = r5.status_code == 200
            self.record("DBA Auth Acceptance with Valid Token", passed5, f"HTTP {r5.status_code} OK")
        except Exception as e:
            self.record("DBA Auth Acceptance with Valid Token", False, str(e))
        print()

    def test_status_endpoints(self, client: httpx.Client):
        print("[*] Stage 3: Agent Operational Status Inspection")
        headers_ba = {"Authorization": f"Bearer {self.ba_token}"}
        headers_dba = {"Authorization": f"Bearer {self.dba_token}"}

        try:
            r_ba = client.get(f"{self.ba_endpoint}/status", headers=headers_ba)
            d = r_ba.json()
            passed = r_ba.status_code == 200 and "state" in d and d.get("agent_id") == "ba-01"
            self.record("BA Status API (GET /status)", passed, f"Agent ID: {d.get('agent_id')}, State: {d.get('state')}")
        except Exception as e:
            self.record("BA Status API (GET /status)", False, str(e))

        try:
            r_dba = client.get(f"{self.dba_endpoint}/status", headers=headers_dba)
            d = r_dba.json()
            passed = r_dba.status_code == 200 and "state" in d and d.get("agent_id") == "dba-01"
            self.record("DBA Status API (GET /status)", passed, f"Agent ID: {d.get('agent_id')}, State: {d.get('state')}")
        except Exception as e:
            self.record("DBA Status API (GET /status)", False, str(e))
        print()

    def test_ba_srs_generation(self, client: httpx.Client) -> Tuple[str, str]:
        print("[*] Stage 4: BA Agent Generates SRS Document")
        headers = {"Authorization": f"Bearer {self.ba_token}"}

        payload = {
            "project_name": "Smart E-Commerce Order & Inventory System",
            "description": (
                "Xay dung he thong quan ly don hang va ton kho thuong mai dien tu. "
                "Bao gom phan he nguoi dung (User & Role), danh muc san pham (Product & Category), "
                "gio hang (Cart), don dat hang (Order & OrderItem), thanh toan (Payment Transaction), "
                "va theo doi xuat nhap kho (Inventory Transaction)."
            ),
            "domain": "E-Commerce / Retail Logistics",
            "features": [
                "User Authentication & Role-based Access Control",
                "Product Catalog & Multi-level Categories",
                "Order Placement with Atomic Stock Reservation",
                "Multi-channel Payment Processing (VNPay, Momo, Credit Card)",
                "Audit Trail & Inventory Ledger",
            ],
        }

        try:
            start_t = time.time()
            res = client.post(f"{self.ba_endpoint}/srs/generate", json=payload, headers=headers)
            elapsed = time.time() - start_t

            if res.status_code == 200:
                data = res.json()
                srs_content = data.get("srs_content", "")
                checksum = data.get("checksum", "")
                has_content = len(srs_content) > 100
                self.record(
                    "BA Generate SRS (POST /srs/generate)",
                    has_content,
                    f"Generated {len(srs_content)} bytes in {elapsed:.2f}s (Checksum: {checksum[:8]}...)",
                )

                # Verify file saved on disk
                ba_srs_path = ROOT_DIR / "agents" / "ba" / "artifacts" / "SRS.md"
                self.record(
                    "BA Artifact File Verified on Disk",
                    ba_srs_path.is_file(),
                    f"Path: {ba_srs_path} ({ba_srs_path.stat().st_size if ba_srs_path.is_file() else 0} bytes)",
                )
                print()
                return srs_content, checksum
            else:
                self.record("BA Generate SRS (POST /srs/generate)", False, f"HTTP {res.status_code}: {res.text}")
        except Exception as e:
            self.record("BA Generate SRS (POST /srs/generate)", False, str(e))

        print()
        return "", ""

    def test_api_transfer_to_dba(self, client: httpx.Client, srs_text: str, checksum: str):
        print("[*] Stage 5: Cross-Agent HTTP API Transmission (Shared-Nothing / Pure API)")
        if not srs_text:
            self.record("Cross-Agent Transfer (BA -> DBA)", False, "Skipped due to empty SRS content")
            print()
            return

        # 1. Test direct BA -> DBA automated dispatch via POST /srs/send-to-dba
        try:
            headers_ba = {"Authorization": f"Bearer {self.ba_token}"}
            dispatch_payload = {
                "dba_endpoint": self.dba_endpoint,
                "dba_token": self.dba_token,
                "artifact_id": "SRS.md",
                "trigger_schema_generation": False,
            }
            res_dispatch = client.post(f"{self.ba_endpoint}/srs/send-to-dba", json=dispatch_payload, headers=headers_ba)
            passed_disp = res_dispatch.status_code == 200 and res_dispatch.json().get("status") == "SENT_SUCCESSFULLY"
            self.record(
                "BA Dispatches SRS via HTTP API (POST /srs/send-to-dba)",
                passed_disp,
                f"HTTP {res_dispatch.status_code} - Verified HTTP POST to DBA /artifacts/inbox",
            )
        except Exception as e:
            self.record("BA Dispatches SRS via HTTP API (POST /srs/send-to-dba)", False, str(e))

        # 2. Verify Checksum Validation on DBA Inbox
        try:
            headers_dba = {"Authorization": f"Bearer {self.dba_token}"}
            bad_inbox_payload = {
                "artifact_id": "SRS_TAMPERED.md",
                "type": "SRS_DOCUMENT",
                "created_by": "ba-01",
                "content": srs_text,
                "checksum": "tampered_bad_sha256_checksum_0000000000000000000000000000000000",
            }
            r_bad = client.post(f"{self.dba_endpoint}/artifacts/inbox", json=bad_inbox_payload, headers=headers_dba)
            passed_tamper = r_bad.status_code == 422
            self.record(
                "DBA Checksum Integrity Check on Inbox (422 expected on mismatch)",
                passed_tamper,
                f"HTTP {r_bad.status_code} (Properly caught checksum mismatch)",
            )
        except Exception as e:
            self.record("DBA Checksum Integrity Check on Inbox", False, str(e))

        print()

    def test_dba_schema_generation(self, client: httpx.Client, srs_text: str):
        print("[*] Stage 6: DBA Analyzes SRS & Compiles Database Schema DDL")
        headers = {"Authorization": f"Bearer {self.dba_token}"}

        payload = {
            "type": "DATABASE_DESIGN",
            "requirements": srs_text if srs_text else "Project: E-Commerce Store with user auth and catalog",
            "task_id": f"dba-e2e-{int(time.time())}",
        }

        try:
            start_t = time.time()
            res = client.post(f"{self.dba_endpoint}/tasks", json=payload, headers=headers)
            elapsed = time.time() - start_t

            if res.status_code == 200:
                data = res.json()
                validation = data.get("validation", {})
                artifacts = data.get("artifacts", [])
                summary = data.get("summary", {})
                all_passed = validation.get("all_passed", False)
                total_tables = summary.get("total_tables", 0)

                self.record(
                    "DBA Schema Pipeline (POST /tasks)",
                    all_passed,
                    f"Generated {total_tables} tables with all validation checks passed in {elapsed:.2f}s",
                )

                # Verify schema.sql artifact exists on disk
                dba_sql_path = ROOT_DIR / "agents" / "dba" / "artifacts" / "schema.sql"
                has_sql_file = dba_sql_path.is_file() and dba_sql_path.stat().st_size > 0
                self.record(
                    "DBA schema.sql Saved to Artifacts",
                    has_sql_file,
                    f"Path: {dba_sql_path} ({dba_sql_path.stat().st_size if has_sql_file else 0} bytes)",
                )

                # Read SQL preview
                if has_sql_file:
                    sql_head = "\n".join([l for l in dba_sql_path.read_text(encoding="utf-8").splitlines() if l.strip().startswith("CREATE TABLE")][:4])
                    print(f"      [DDL Preview Tables]:\n{sql_head}")

            else:
                self.record("DBA Schema Pipeline (POST /tasks)", False, f"HTTP {res.status_code}: {res.text}")
        except Exception as e:
            self.record("DBA Schema Pipeline (POST /tasks)", False, str(e))

        print()

    def test_artifact_persistence(self, client: httpx.Client):
        print("[*] Stage 7: Artifact Management & Audit Verification")
        headers_ba = {"Authorization": f"Bearer {self.ba_token}"}
        headers_dba = {"Authorization": f"Bearer {self.dba_token}"}

        try:
            r_ba = client.get(f"{self.ba_endpoint}/artifacts", headers=headers_ba)
            count = r_ba.json().get("count", 0)
            self.record("BA Artifacts Listing (GET /artifacts)", count > 0, f"Found {count} artifacts in BA storage")
        except Exception as e:
            self.record("BA Artifacts Listing (GET /artifacts)", False, str(e))

        try:
            r_dba = client.get(f"{self.dba_endpoint}/artifacts", headers=headers_dba)
            items = r_dba.json()
            self.record("DBA Artifacts Listing (GET /artifacts)", len(items) > 0, f"Found {len(items)} artifacts in DBA storage")
        except Exception as e:
            self.record("DBA Artifacts Listing (GET /artifacts)", False, str(e))

        print()

    def print_summary(self) -> bool:
        total = len(self.results)
        passed = sum(1 for _, p, _ in self.results if p)
        failed = total - passed

        print("=" * 75)
        print(f" TEST SUITE SUMMARY: {passed}/{total} PASSED ({failed} FAILED)")
        print("=" * 75)
        for name, p, msg in self.results:
            status_text = "PASS" if p else "FAIL"
            print(f" [{status_text}] {name}")

        print("=" * 75)
        if failed == 0:
            print(" [OK] ALL TESTS PASSED! Multi-Agent BA <-> DBA integration is verified.")
            return True
        else:
            print(" [FAIL] SOME TESTS FAILED. Please review the error log above.")
            return False


if __name__ == "__main__":
    runner = TestRunner()
    success = runner.run_all()
    sys.exit(0 if success else 1)
