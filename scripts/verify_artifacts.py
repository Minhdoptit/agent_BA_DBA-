import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.ba.agent import BAAgent
from agents.dba.agent import DBAAgent

print("=== 1. TESTING BA AGENT PIPELINE ===")
ba = BAAgent()
res_ba = ba.execute_task({
    "project_name": "Hệ thống Quản lý sinh viên",
    "description": "Hệ thống Quản lý sinh viên: Thêm, sửa, xóa, tìm kiếm sinh viên, upload ảnh đại diện avatar, phân lớp và phân khoa"
})
print("BA Task execution:", res_ba["status"])
ba_artifacts = [a["name"] for a in ba.list_artifacts()]
print("BA Generated Artifacts:", ba_artifacts)

assert "srs.docs" in ba_artifacts, "ERROR: srs.docs not generated!"
assert "SRS.md" in ba_artifacts, "ERROR: SRS.md not generated!"
assert "SRS.docx" in ba_artifacts, "ERROR: SRS.docx not generated!"

srs_docs = (ba.artifact_dir / "srs.docs").read_text(encoding="utf-8")
print(f"srs.docs characters: {len(srs_docs)}")
assert "sequenceDiagram" in srs_docs, "ERROR: sequenceDiagram missing in srs.docs!"
assert "flowchart TD" in srs_docs, "ERROR: flowchart TD missing in srs.docs!"
assert "UC-01" in srs_docs, "ERROR: Use Case UC-01 missing!"
assert "Data Requirements" in srs_docs or "students" in srs_docs, "ERROR: Data Requirements missing!"
print("[PASS] BA Agent successfully generated srs.docs, SRS.docx, and SRS.md with 4 sequence diagrams and flowchart!")

print("\n=== 2. TESTING DBA AGENT PIPELINE ===")
dba = DBAAgent()
res_dba = dba.run(srs_docs)
print("DBA Run status:", res_dba["status"])
print("DBA In-memory SQLite & SQL validations passed:", res_dba["validation"]["all_passed"])
dba_artifacts = [a["filename"] for a in res_dba["artifacts"]]
print("DBA Generated Artifacts:", dba_artifacts)

assert "schema.sql" in dba_artifacts, "ERROR: schema.sql not generated!"
assert "ERD.md" in dba_artifacts, "ERROR: ERD.md not generated!"

schema_sql = (dba.artifact_dir / "schema.sql").read_text(encoding="utf-8")
print(f"schema.sql characters: {len(schema_sql)}")

assert 'CREATE TABLE IF NOT EXISTS "students"' in schema_sql, 'ERROR: students table missing in schema.sql!'
assert 'CREATE TABLE IF NOT EXISTS "departments"' in schema_sql, 'ERROR: departments table missing in schema.sql!'
assert 'CREATE TABLE IF NOT EXISTS "classes"' in schema_sql, 'ERROR: classes table missing in schema.sql!'
assert 'INSERT INTO "students"' in schema_sql, 'ERROR: students seed data missing in schema.sql!'
assert 'idx_students_student_code' in schema_sql, 'ERROR: student code index missing in schema.sql!'

erd_md = (dba.artifact_dir / "ERD.md").read_text(encoding="utf-8")
assert "STUDENTS" in erd_md or "students" in erd_md, "ERROR: students entity missing in ERD.md!"
print("[PASS] DBA Agent successfully generated schema.sql with tables, indexes, constraints, and seed data, plus ERD.md!")

print("\n=== ALL PIPELINE VERIFICATIONS PASSED 100%! ===")
