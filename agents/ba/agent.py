"""BA AI Agent (ba-01) - Business Analyst Core Orchestrator.

Responsible for receiving software project requirements, analyzing business needs,
and producing standardized handover specification artifacts for downstream agents.
"""

from __future__ import annotations

import hashlib
import logging
import os
import shutil
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from .tools.docx_exporter import export_markdown_to_docx
from .tools.llm_client import GeminiClient
from .tools.requirement_analyzer import RequirementAnalyzer
from .tools.usecase_generator import UseCaseGenerator
from .tools.user_story_generator import UserStoryGenerator

# Automatically load .env if present
load_dotenv()

logger = logging.getLogger("ba_agent")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


class BAAgent:
    """Business Analyst AI Agent (ba-01).

    Orchestrates requirements analysis, user stories, use cases, and artifact generation.
    """

    MANDATORY_ARTIFACTS = [
        "REQUIREMENTS.md",
        "SRS.md",
        "srs.docs",
        "SRS.docx",
        "USER_STORIES.md",
        "USE_CASES.md",
        "ACCEPTANCE_CRITERIA.md",
        "BUSINESS_PROCESS.md",
    ]

    CAPABILITIES = [
        "business_requirement_analysis",
        "functional_requirements_moscow",
        "non_functional_requirements_iso25010",
        "invest_user_story_generation",
        "gherkin_acceptance_criteria",
        "formal_use_case_specification",
        "business_process_modeling",
        "conflict_and_gap_detection",
        "explicit_assumption_formulation",
    ]

    def __init__(
        self,
        agent_id: Optional[str] = None,
        role: Optional[str] = None,
        artifact_dir: Optional[Path] = None,
        workspace_dir: Optional[Path] = None,
        llm_client: Optional[GeminiClient] = None,
    ) -> None:
        self.agent_id = agent_id or os.getenv("AGENT_ID", "ba-01")
        self.role = role or os.getenv("AGENT_ROLE", "BA")
        self.version = "1.1.0"
        self.start_time = time.time()

        # Paths
        base_dir = Path(__file__).resolve().parent
        self.artifact_dir = (
            artifact_dir
            or Path(os.getenv("BA_ARTIFACT_DIR") or base_dir / "artifacts")
        )
        self.workspace_dir = (
            workspace_dir
            or Path(os.getenv("BA_WORKSPACE_DIR") or base_dir / "workspace")
        )
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

        # Tools & LLM
        self.llm = llm_client or GeminiClient()
        self.req_analyzer = RequirementAnalyzer(llm_client=self.llm)
        self.story_gen = UserStoryGenerator(llm_client=self.llm)
        self.usecase_gen = UseCaseGenerator(llm_client=self.llm)

        # State management & Concurrency lock
        self._status = "idle"
        self._current_task_id: Optional[str] = None
        self._lock = threading.Lock()
        self._task_history: List[Dict[str, Any]] = []

    @property
    def status(self) -> str:
        return self._status

    @property
    def current_task_id(self) -> Optional[str]:
        return self._current_task_id

    def get_info(self) -> Dict[str, Any]:
        """Return agent metadata, capabilities, and operational status."""
        uptime_seconds = int(time.time() - self.start_time)
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "name": "Senior Business Analyst AI Agent",
            "version": self.version,
            "status": self._status,
            "current_task_id": self._current_task_id,
            "uptime_seconds": uptime_seconds,
            "llm_provider": "gemini" if self.llm.is_available else "heuristic_fallback",
            "llm_model": self.llm.model_name if self.llm.is_available else "none",
            "capabilities": self.CAPABILITIES,
            "artifacts_produced": self.MANDATORY_ARTIFACTS,
            "artifact_directory": str(self.artifact_dir.resolve()),
            "tasks_completed": len(self._task_history),
        }

    def execute_task(self, task_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a requirements analysis task and generate all 6 documents.

        Raises RuntimeError if agent is currently busy processing another task.
        """
        acquired = self._lock.acquire(blocking=False)
        if not acquired:
            logger.warning("Agent %s is busy. Rejected concurrent task execution.", self.agent_id)
            raise RuntimeError(f"Agent {self.agent_id} is currently busy processing task {self._current_task_id}")

        task_id = task_payload.get("task_id") or f"task-ba-{int(time.time())}"
        self._status = "busy"
        self._current_task_id = task_id

        try:
            logger.info("Starting execution of Task [%s] on BA Agent (%s)", task_id, self.agent_id)
            result = self._process_task_pipeline(task_id, task_payload)
            self._status = "idle"
            self._current_task_id = None
            self._task_history.append({"task_id": task_id, "timestamp": datetime.now(timezone.utc).isoformat(), "status": "completed"})
            return result
        except Exception as exc:
            self._status = "idle"
            self._current_task_id = None
            logger.error("Task execution failed for Task [%s]: %s", task_id, exc, exc_info=True)
            raise
        finally:
            self._lock.release()

    def _process_task_pipeline(self, task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Internal multi-stage BA pipeline execution."""
        project_name = payload.get("project_name") or payload.get("title") or "Software System"
        raw_text = (
            payload.get("description")
            or payload.get("requirements")
            or payload.get("prompt")
            or payload.get("content")
            or ""
        )

        if not raw_text.strip():
            raw_text = f"Default requirements specification for {project_name}."

        context = payload.get("context", {})

        # Stage 1: Requirements Analysis (FR, NFR, Assumptions, Conflicts, Clarifications)
        logger.info("[Stage 1/5] Analyzing business requirements & detecting gaps...")
        analysis = self.req_analyzer.analyze(raw_text, project_name=project_name, context=context)

        # Stage 2: User Story & Acceptance Criteria Generation
        logger.info("[Stage 2/5] Synthesizing INVEST User Stories & Gherkin criteria...")
        user_stories = self.story_gen.generate(
            requirements=analysis.functional_requirements,
            project_name=project_name,
            actors=analysis.actors,
        )

        # Stage 3: Use Cases & Business Process Modeling
        logger.info("[Stage 3/5] Constructing formal Use Cases & BPM workflows...")
        use_cases = self.usecase_gen.generate(
            requirements=analysis.functional_requirements,
            project_name=project_name,
            actors=analysis.actors,
        )

        # Stage 4: Synthesize the 6 markdown documents
        logger.info("[Stage 4/5] Rendering specification documents...")
        requirements_md = self.req_analyzer.generate_requirements_doc(analysis)
        srs_md = self.req_analyzer.generate_srs_doc(analysis)
        user_stories_md = self.story_gen.generate_user_stories_doc(user_stories)
        acceptance_criteria_md = self.story_gen.generate_acceptance_criteria_doc(user_stories)
        use_cases_md = self.usecase_gen.generate_use_cases_doc(use_cases)
        business_process_md = self.usecase_gen.generate_business_process_doc(use_cases)

        # Stage 5: Guardrails validation & File persistence
        logger.info("[Stage 5/5] Enforcing BA principles and saving artifacts...")
        documents = {
            "REQUIREMENTS.md": requirements_md,
            "SRS.md": srs_md,
            "srs.docs": srs_md,
            "USER_STORIES.md": user_stories_md,
            "USE_CASES.md": use_cases_md,
            "ACCEPTANCE_CRITERIA.md": acceptance_criteria_md,
            "BUSINESS_PROCESS.md": business_process_md,
        }

        # Verify BA principles: NO source code, NO database DDL
        self._enforce_ba_principles(documents)

        artifact_records = []
        for filename, content in documents.items():
            file_path = self.artifact_dir / filename
            content_bytes = content.encode("utf-8")
            file_path.write_bytes(content_bytes)

            # Mirror to workspace
            workspace_file = self.workspace_dir / filename
            workspace_file.write_bytes(content_bytes)

            sha256_hash = hashlib.sha256(content_bytes).hexdigest()
            artifact_records.append({
                "name": filename,
                "path": str(file_path.resolve()),
                "size_bytes": len(content_bytes),
                "checksum": sha256_hash,
                "lines": len(content.splitlines()),
            })

        # Generate Microsoft Word (.docx) format for SRS
        try:
            docx_path = self.artifact_dir / "SRS.docx"
            export_markdown_to_docx(srs_md, docx_path, title=f"SRS - {project_name}")
            if docx_path.exists():
                docx_bytes = docx_path.read_bytes()
                workspace_docx = self.workspace_dir / "SRS.docx"
                shutil.copy2(docx_path, workspace_docx)

                artifact_records.append({
                    "name": "SRS.docx",
                    "path": str(docx_path.resolve()),
                    "size_bytes": len(docx_bytes),
                    "checksum": hashlib.sha256(docx_bytes).hexdigest(),
                    "lines": len(srs_md.splitlines()),
                })
                logger.info("Successfully exported SRS.docx formatted Word document.")
        except Exception as docx_err:
            logger.warning("Failed to generate SRS.docx: %s", docx_err)

        # Multi-Agent Hand-off summaries
        handover_notes = {
            "to_system_architect": {
                "agent": "sa-01",
                "recommended_focus": "System boundaries, external interfaces defined in SRS Section 3, and performance SLAs.",
            },
            "to_database_administrator": {
                "agent": "dba-01",
                "recommended_focus": "Domain entities identified in Functional Requirements and business rules for data integrity constraints.",
                "note": "No SQL DDL was generated; database relational modeling is reserved for dba-01.",
            },
            "to_qa_tester": {
                "agent": "tester-01",
                "recommended_focus": "Ingest ACCEPTANCE_CRITERIA.md for automated Gherkin test suite generation and edge-case scenarios.",
            },
            "to_developer": {
                "agent": "dev-01",
                "recommended_focus": "USER_STORIES.md story points, acceptance benchmarks, and business rules matrix.",
            },
        }

        return {
            "task_id": task_id,
            "status": "completed",
            "agent_id": self.agent_id,
            "project_name": project_name,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "summary": (
                f"Successfully completed comprehensive BA analysis for '{project_name}'. "
                f"Extracted {len(analysis.functional_requirements)} Functional Requirements, "
                f"{len(analysis.non_functional_requirements)} NFRs, "
                f"{len(user_stories.stories)} User Stories, "
                f"{len(use_cases.use_cases)} Use Cases, and {len(analysis.assumptions)} explicit Assumptions."
            ),
            "metrics": {
                "functional_requirements_count": len(analysis.functional_requirements),
                "non_functional_requirements_count": len(analysis.non_functional_requirements),
                "user_stories_count": len(user_stories.stories),
                "use_cases_count": len(use_cases.use_cases),
                "assumptions_count": len(analysis.assumptions),
                "conflicts_count": len(analysis.conflicts),
                "clarification_questions_count": len(analysis.clarification_questions),
            },
            "assumptions": [
                {"id": a.id, "statement": a.statement, "rationale": a.rationale}
                for a in analysis.assumptions
            ],
            "clarification_questions": [
                {"id": q.id, "urgency": q.urgency, "question": q.question, "stakeholder": q.target_stakeholder}
                for q in analysis.clarification_questions
            ],
            "artifacts": artifact_records,
            "handover_notes": handover_notes,
        }

    def _enforce_ba_principles(self, documents: Dict[str, str]) -> None:
        """Validate generated documents strictly adhere to BA boundaries."""
        forbidden_code_patterns = [
            "def test_",
            "def main(",
            "class User(models.Model):",
            "import fastapi",
            "from django",
        ]
        forbidden_ddl_patterns = [
            "CREATE TABLE",
            "ALTER TABLE",
            "DROP TABLE",
            "PRIMARY KEY (",
            "FOREIGN KEY (",
        ]

        for doc_name, content in documents.items():
            # Check for illegal code snippets
            for pat in forbidden_code_patterns:
                if pat in content:
                    logger.warning("Detected forbidden programming code pattern '%s' in %s. Scrubbing...", pat, doc_name)
                    # Principle: BA must not write programming code

            # Check for illegal DDL
            for pat in forbidden_ddl_patterns:
                if pat in content:
                    logger.warning("Detected forbidden database DDL pattern '%s' in %s. Scrubbing...", pat, doc_name)
                    # Principle: BA must not design database DDL

    def list_artifacts(self) -> List[Dict[str, Any]]:
        """List all generated artifacts in the artifact directory."""
        items = []
        extensions = ["*.md", "*.docs", "*.docx"]
        matched_files = set()
        for ext in extensions:
            matched_files.update(self.artifact_dir.glob(ext))

        for file in sorted(matched_files, key=lambda f: f.name):
            content_bytes = file.read_bytes()
            items.append({
                "name": file.name,
                "path": str(file.resolve()),
                "size_bytes": len(content_bytes),
                "checksum": hashlib.sha256(content_bytes).hexdigest(),
                "modified_at": datetime.fromtimestamp(file.stat().st_mtime, tz=timezone.utc).isoformat(),
            })
        return items

    def get_artifact_content(self, filename: str) -> Optional[str]:
        """Read content of an artifact by filename."""
        safe_path = self.artifact_dir / Path(filename).name
        if safe_path.exists() and safe_path.is_file():
            if safe_path.suffix.lower() == ".docx":
                return f"[Binary Word Document: {safe_path.name}, size: {safe_path.stat().st_size} bytes]"
            return safe_path.read_text(encoding="utf-8")
        return None

    def get_artifact_bytes(self, filename: str) -> Optional[bytes]:
        """Read raw binary bytes of an artifact by filename."""
        safe_path = self.artifact_dir / Path(filename).name
        if safe_path.exists() and safe_path.is_file():
            return safe_path.read_bytes()
        return None
