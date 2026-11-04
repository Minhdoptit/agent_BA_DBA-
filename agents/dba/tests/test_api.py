"""Unit and integration tests for FastAPI application in api.py."""

import os
import pytest
from fastapi.testclient import TestClient

from agents.dba.api import app

client = TestClient(app)


@pytest.fixture
def auth_headers():
    token = os.getenv("AGENT_API_KEY", "")
    return {"Authorization": f"Bearer {token}"} if token else {}


def test_get_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OK"
    assert data["agent_id"] == "dba-01"
    assert data["agent_role"] == "DBA"
    assert "version" in data
    assert "timestamp" in data


def test_get_agent_metadata(auth_headers):
    response = client.get("/agent", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["agent_id"] == "dba-01"
    assert data["agent_role"] == "DBA"
    assert "capabilities" in data
    assert "mandatory_outputs" in data
    assert "schema.sql" in data["mandatory_outputs"]
    assert "ERD.md" in data["mandatory_outputs"]


def test_get_state(auth_headers):
    response = client.get("/state", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["agent_id"] == "dba-01"
    assert data["status"] in ["IDLE", "BUSY"]


def test_post_tasks_generates_all_artifacts(auth_headers):
    task_payload = {
        "task_id": "test_api_task_001",
        "requirements": """
        # Project: MediCare Health Portal
        [FR-01] Patient and Doctor account authentication with roles.
        [FR-02] Medical departments and service catalog.
        [FR-03] Appointment bookings and consultation slots.
        [FR-04] Medical prescription payment invoices.
        [FR-05] HIPAA compliance audit logging.
        """,
    }
    response = client.post("/tasks", json=task_payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["task_id"] == "test_api_task_001"
    assert data["status"] == "SUCCESS"
    assert data["agent_id"] == "dba-01"
    assert len(data["artifacts"]) == 6

    artifact_names = [a["filename"] for a in data["artifacts"]]
    assert "DATA_REQUIREMENTS.md" in artifact_names
    assert "ERD.md" in artifact_names
    assert "DATABASE_DESIGN.md" in artifact_names
    assert "schema.sql" in artifact_names
    assert "INDEX_STRATEGY.md" in artifact_names
    assert "DATABASE_REVIEW.md" in artifact_names


def test_get_artifacts_list(auth_headers):
    response = client.get("/artifacts", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    filenames = [item["filename"] for item in data]
    assert "schema.sql" in filenames


def test_get_artifact_content(auth_headers):
    response = client.get("/artifacts/schema.sql/content", headers=auth_headers)
    assert response.status_code == 200
    assert "CREATE TABLE" in response.text
    assert "X-Checksum-SHA256" in response.headers


def test_post_artifacts_inbox(auth_headers):
    payload = {
        "artifact_id": "inbox_test_req.md",
        "type": "DOCUMENTATION",
        "created_by": "ba-01",
        "content": "# Test requirements from BA",
    }
    response = client.post("/artifacts/inbox", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ACCEPTED"
    assert "checksum" in data
