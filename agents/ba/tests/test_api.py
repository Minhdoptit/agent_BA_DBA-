"""API integration tests using FastAPI TestClient."""

import os
from fastapi.testclient import TestClient
import pytest
from agents.ba.api import app, ba_agent


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["agent_id"] == "ba-01"
    assert data["role"] == "BA"
    assert "timestamp" in data
    assert data["uptime_seconds"] >= 0


def test_agent_endpoint(client):
    response = client.get("/agent")
    assert response.status_code == 200
    data = response.json()
    assert data["agent_id"] == "ba-01"
    assert data["role"] == "BA"
    assert "capabilities" in data
    assert "REQUIREMENTS.md" in data["artifacts_produced"]
    assert len(data["artifacts_produced"]) == 6


def test_create_task_endpoint(client):
    payload = {
        "task_id": "api-task-001",
        "project_name": "Warehouse Inventory Management",
        "description": (
            "Hệ thống quản lý kho thông minh cho chuỗi bán lẻ:\n"
            "- Nhập kho, xuất kho, kiểm kê định kỳ với mã vạch QR code.\n"
            "- Cảnh báo tồn kho tối thiểu và tự động đề xuất đơn đặt hàng mới.\n"
            "- Phân quyền cho Thủ kho, Nhân viên bốc dỡ, và Quản lý logistics.\n"
            "- Báo cáo doanh số và tỷ lệ thất thoát theo tháng.\n"
        ),
    }

    response = client.post("/tasks", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["task_id"] == "api-task-001"
    assert len(data["artifacts"]) == 6
    assert "assumptions" in data
    assert "clarification_questions" in data
    assert "handover_notes" in data


def test_list_and_get_artifacts(client):
    # First list artifacts
    response = client.get("/artifacts")
    assert response.status_code == 200
    data = response.json()
    assert "artifacts" in data
    assert data["count"] >= 6

    # Download one artifact
    res_art = client.get("/artifacts/REQUIREMENTS.md")
    assert res_art.status_code == 200
    assert "text/markdown" in res_art.headers.get("content-type", "")
    assert len(res_art.text) > 100

    # Non-existent artifact
    res_404 = client.get("/artifacts/UNKNOWN_FILE.md")
    assert res_404.status_code == 404


def test_inbox_upload_endpoint(client):
    payload = {
        "filename": "project_brief.md",
        "content": "# Brief from PM\nPlease design the requirements for the system.",
        "source_agent": "pm-01",
        "artifact_type": "BRIEF",
    }
    response = client.post("/artifacts/inbox", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "received"
    assert data["filename"] == "project_brief.md"
    assert "checksum" in data


def test_bearer_token_authentication(monkeypatch, client):
    # Set AGENT_API_KEY to test authentication protection
    monkeypatch.setenv("AGENT_API_KEY", "super_secret_token_12345")

    # 1. Unauthenticated request to /agent should fail with 401
    res_no_auth = client.get("/agent")
    assert res_no_auth.status_code == 401

    # 2. Invalid token should fail with 401
    res_bad_auth = client.get("/agent", headers={"Authorization": "Bearer wrong_token"})
    assert res_bad_auth.status_code == 401

    # 3. Valid token should succeed with 200
    res_good_auth = client.get("/agent", headers={"Authorization": "Bearer super_secret_token_12345"})
    assert res_good_auth.status_code == 200

    # 4. /health endpoint remains open (no auth required)
    res_health = client.get("/health")
    assert res_health.status_code == 200
