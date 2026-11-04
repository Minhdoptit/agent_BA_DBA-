"""End-to-End integration tests for DBAAgent."""

import shutil
from pathlib import Path
import pytest

from agents.dba.agent import DBAAgent


@pytest.fixture
def temp_agent(tmp_path):
    workspace = tmp_path / "workspace"
    artifacts = tmp_path / "artifacts"
    agent = DBAAgent(
        workspace_dir=str(workspace),
        artifact_dir=str(artifacts),
    )
    return agent, workspace, artifacts


def test_dba_agent_e2e_execution(temp_agent):
    agent, workspace, artifacts = temp_agent

    sample_srs = """
    # Project: FastFood Delivery Network
    ## Business Requirements from BA (ba-01)
    [FR-01] User and Courier account registration with password encryption.
    [FR-02] Menu categories and food dishes with prices and inventory.
    [FR-03] Order placement with line item dish snapshots.
    [FR-04] Payment gateway transactions via digital wallet or card.
    [FR-05] Audit logging of sensitive status changes.
    """

    result = agent.run(sample_srs)

    # 1. Status check
    assert result["status"] == "SUCCESS"
    assert result["agent_id"] == "dba-01"
    assert result["agent_role"] == "DBA"
    assert result["validation"]["all_passed"] is True
    assert result["validation"]["in_memory_execution"]["passed"] is True

    # 2. Check all 6 mandatory artifacts
    mandatory_filenames = [
        "DATA_REQUIREMENTS.md",
        "ERD.md",
        "DATABASE_DESIGN.md",
        "schema.sql",
        "INDEX_STRATEGY.md",
        "DATABASE_REVIEW.md",
    ]

    generated_filenames = [a["filename"] for a in result["artifacts"]]
    for m in mandatory_filenames:
        assert m in generated_filenames, f"Missing mandatory artifact: {m}"
        # File must exist in artifact_dir and workspace_dir
        assert (artifacts / m).is_file(), f"File {m} does not exist in artifacts dir"
        assert (workspace / m).is_file(), f"File {m} does not exist in workspace dir"

    # 3. Check schema.sql content
    schema_sql_content = (artifacts / "schema.sql").read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS" in schema_sql_content
    assert "users" in schema_sql_content
    assert "orders" in schema_sql_content
    assert "order_items" in schema_sql_content
    assert "payments" in schema_sql_content
    assert "audit_logs" in schema_sql_content
    assert "PRIMARY KEY" in schema_sql_content
    assert "FOREIGN KEY" in schema_sql_content

    # 4. Check ERD.md content
    erd_content = (artifacts / "ERD.md").read_text(encoding="utf-8")
    assert "erDiagram" in erd_content
    assert "USERS ||--" in erd_content

    # 5. Check DATABASE_REVIEW.md content
    review_content = (artifacts / "DATABASE_REVIEW.md").read_text(encoding="utf-8")
    assert "Traceability Matrix" in review_content
    assert "FR-01" in review_content
    assert "SQL Safety & Destructive Command Audit" in review_content
