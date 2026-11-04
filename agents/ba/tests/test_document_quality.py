"""Document quality and rule compliance validation tests."""

import re
from pathlib import Path
import pytest
from agents.ba.agent import BAAgent


@pytest.fixture(scope="module")
def executed_agent(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("ba_quality_test")
    art_dir = tmp_path / "artifacts"
    ws_dir = tmp_path / "workspace"
    agent = BAAgent(agent_id="ba-01", role="BA", artifact_dir=art_dir, workspace_dir=ws_dir)

    payload = {
        "task_id": "quality-check-001",
        "project_name": "Food Delivery Express",
        "description": (
            "Dự án Nền tảng Giao đồ ăn trực tuyến Food Delivery Express:\n"
            "- Khách hàng chọn món từ các nhà hàng lân cận, thêm vào giỏ hàng và thanh toán.\n"
            "- Tài xế (Shipper) nhận đơn giao hàng, cập nhật vị trí thời gian thực.\n"
            "- Nhà hàng quản lý thực đơn, nhận đơn hàng và xác nhận chuẩn bị món.\n"
            "- Quản trị viên đối soát hoa hồng và xử lý khiếu nại khách hàng.\n"
            "- Yêu cầu hệ thống phản hồi cực nhanh dưới 500ms, đảm bảo bảo mật thanh toán.\n"
        ),
    }
    agent.execute_task(payload)
    return agent


def test_requirements_md_quality(executed_agent: BAAgent):
    content = executed_agent.get_artifact_content("REQUIREMENTS.md")
    assert content is not None

    # Check MoSCoW priority presence
    assert "MoSCoW Priority" in content
    assert "Must Have" in content

    # Check ISO 25010 NFRs
    assert "Performance" in content or "Security" in content

    # Check explicit Assumptions
    assert "Assumptions Register" in content
    assert "[ASSUMPTION-" in content

    # Check Clarification Questions
    assert "Clarification Questions" in content
    assert "[Q-" in content


def test_srs_md_quality(executed_agent: BAAgent):
    content = executed_agent.get_artifact_content("SRS.md")
    assert content is not None

    # Check IEEE 830 sections
    assert "IEEE 830" in content
    assert "1. Introduction" in content
    assert "2. Overall Description" in content
    assert "3. External Interface Requirements" in content
    assert "4. System Features" in content
    assert "5. Non-Functional Requirements" in content
    assert "Traceability Matrix" in content


def test_user_stories_md_quality(executed_agent: BAAgent):
    content = executed_agent.get_artifact_content("USER_STORIES.md")
    assert content is not None

    # Check INVEST and Story format
    assert "INVEST" in content
    assert "As a" in content
    assert "I want" in content
    assert "So that" in content
    assert "Story Points" in content


def test_acceptance_criteria_md_quality(executed_agent: BAAgent):
    content = executed_agent.get_artifact_content("ACCEPTANCE_CRITERIA.md")
    assert content is not None

    # Check strict Gherkin structure
    assert "Feature:" in content
    assert "Scenario:" in content
    assert "Given" in content
    assert "When" in content
    assert "Then" in content


def test_use_cases_md_quality(executed_agent: BAAgent):
    content = executed_agent.get_artifact_content("USE_CASES.md")
    assert content is not None

    # Check formal Use Case sections
    assert "Actor Catalog" in content
    assert "Primary Actor" in content
    assert "Main Success Scenario" in content
    assert "Alternative Flows" in content
    assert "Exception / Failure Flows" in content
    assert "Postconditions" in content


def test_business_process_md_quality(executed_agent: BAAgent):
    content = executed_agent.get_artifact_content("BUSINESS_PROCESS.md")
    assert content is not None

    # Check Process Workflow and Mermaid Diagram
    assert "```mermaid" in content
    assert "flowchart TD" in content
    assert "Swimlane" in content or "RACI" in content


def test_strict_ba_boundaries_no_code_and_no_sql_ddl(executed_agent: BAAgent):
    all_artifacts = [
        "REQUIREMENTS.md",
        "SRS.md",
        "USER_STORIES.md",
        "USE_CASES.md",
        "ACCEPTANCE_CRITERIA.md",
        "BUSINESS_PROCESS.md",
    ]

    for fname in all_artifacts:
        doc = executed_agent.get_artifact_content(fname)
        assert doc is not None

        # Principle 1: BA does NOT write programming code
        assert "```python" not in doc, f"Forbidden python code block found in {fname}"
        assert "```javascript" not in doc, f"Forbidden javascript code block found in {fname}"
        assert "def test_" not in doc, f"Forbidden function definition in {fname}"

        # Principle 2: BA does NOT design database schemas/DDL
        assert "CREATE TABLE" not in doc, f"Forbidden SQL CREATE TABLE in {fname}"
        assert "ALTER TABLE" not in doc, f"Forbidden SQL ALTER TABLE in {fname}"
        assert "DROP TABLE" not in doc, f"Forbidden SQL DROP TABLE in {fname}"
        assert "PRIMARY KEY (" not in doc, f"Forbidden SQL PRIMARY KEY DDL in {fname}"
