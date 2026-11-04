"""Integration tests for BAAgent core orchestrator."""

import threading
import time
from pathlib import Path
import pytest
from agents.ba.agent import BAAgent


def test_agent_initialization(tmp_path: Path):
    art_dir = tmp_path / "artifacts"
    ws_dir = tmp_path / "workspace"
    agent = BAAgent(agent_id="ba-01", role="BA", artifact_dir=art_dir, workspace_dir=ws_dir)

    info = agent.get_info()
    assert info["agent_id"] == "ba-01"
    assert info["role"] == "BA"
    assert info["status"] == "idle"
    assert "REQUIREMENTS.md" in info["artifacts_produced"]
    assert len(info["artifacts_produced"]) == 6


def test_agent_task_execution_produces_all_6_artifacts(tmp_path: Path):
    art_dir = tmp_path / "artifacts"
    ws_dir = tmp_path / "workspace"
    agent = BAAgent(agent_id="ba-01", role="BA", artifact_dir=art_dir, workspace_dir=ws_dir)

    task_payload = {
        "task_id": "task-test-001",
        "project_name": "Clinic Booking System",
        "description": (
            "Hệ thống đặt lịch khám bệnh trực tuyến cho phòng khám đa khoa.\n"
            "- Bệnh nhân có thể xem danh sách bác sĩ, chuyên khoa, và lịch trống.\n"
            "- Bệnh nhân đặt lịch hẹn khám và nhận thông báo xác nhận qua SMS/Email.\n"
            "- Bác sĩ xem danh sách lịch khám trong ngày và cập nhật trạng thái đã khám.\n"
            "- Quản lý phòng khám xem thống kê số lượng bệnh nhân và doanh thu.\n"
            "- Hệ thống cần đảm bảo an toàn bảo mật thông tin y tế của bệnh nhân.\n"
        ),
    }

    result = agent.execute_task(task_payload)

    assert result["status"] == "completed"
    assert result["task_id"] == "task-test-001"
    assert len(result["artifacts"]) == 6

    # Verify that all 6 expected files exist physically on disk
    expected_files = [
        "REQUIREMENTS.md",
        "SRS.md",
        "USER_STORIES.md",
        "USE_CASES.md",
        "ACCEPTANCE_CRITERIA.md",
        "BUSINESS_PROCESS.md",
    ]

    for fname in expected_files:
        fpath = art_dir / fname
        assert fpath.exists(), f"File {fname} was not created!"
        assert fpath.stat().st_size > 100, f"File {fname} is unexpectedly small!"

    # Verify handover notes
    assert "to_system_architect" in result["handover_notes"]
    assert "to_database_administrator" in result["handover_notes"]
    assert "to_qa_tester" in result["handover_notes"]
    assert "to_developer" in result["handover_notes"]

    # Verify list_artifacts
    artifacts_list = agent.list_artifacts()
    assert len(artifacts_list) == 6

    # Verify get_artifact_content
    content = agent.get_artifact_content("REQUIREMENTS.md")
    assert content is not None
    assert "Clinic Booking System" in content or "CLINIC" in content


def test_agent_concurrency_lock(tmp_path: Path):
    art_dir = tmp_path / "artifacts"
    ws_dir = tmp_path / "workspace"
    agent = BAAgent(agent_id="ba-01", role="BA", artifact_dir=art_dir, workspace_dir=ws_dir)

    # Artificially lock agent
    acquired = agent._lock.acquire(blocking=False)
    assert acquired is True
    agent._status = "busy"
    agent._current_task_id = "blocking-task"

    try:
        with pytest.raises(RuntimeError) as exc_info:
            agent.execute_task({"project_name": "Test Conflict", "description": "some description"})
        assert "currently busy" in str(exc_info.value)
    finally:
        agent._status = "idle"
        agent._current_task_id = None
        agent._lock.release()
