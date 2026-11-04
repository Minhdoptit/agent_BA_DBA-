"""FastAPI Application for DBA AI Agent (dba-01).

Implements Agent API v1 specifications:
- GET  /health           : Public health check
- GET  /status           : Authenticated status and metrics
- GET  /state            : Current agent busy/idle state
- GET  /agent            : Authenticated agent metadata & capabilities
- POST /tasks            : Ingest requirements & execute database design pipeline
- POST /schema/generate-from-srs : Dedicated endpoint to compile schema from SRS
- GET  /artifacts        : List produced artifacts
- GET  /artifacts/{id}/content : Download/view artifact content
- POST /artifacts/inbox  : Receive artifact from BA or PM agent
"""

from __future__ import annotations

import hashlib
import hmac
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Header, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .agent import DBAAgent
from .logger import setup_logger

BASE_DIR = Path(__file__).resolve().parent
# Load environment variables with local agent directory override
load_dotenv(BASE_DIR / ".env", override=True)
LOGS_DIR = BASE_DIR / "logs"
logger = setup_logger(agent_id="dba-01", log_dir=LOGS_DIR, log_filename="agent_dba.log")

AGENT_ID = os.getenv("DBA_AGENT_ID", "dba-01")
AGENT_ROLE = os.getenv("DBA_AGENT_ROLE", "DBA")
PORT = int(os.getenv("PORT", "8004"))
HOST = os.getenv("HOST", "0.0.0.0")

app = FastAPI(
    title="DBA AI Agent Service (dba-01)",
    version="1.1.0",
    description="Autonomous Senior Database Administrator AI Agent for requirements analysis and database schema engineering.",
)

# HTTP Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000
    logger.info(
        f"HTTP {request.method} {request.url.path} - Status: {response.status_code} ({duration_ms:.1f}ms) [Client: {client_ip}]"
    )
    return response

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Concurrency state
AGENT_STATE = {"status": "IDLE", "current_task_id": None}
STATE_LOCK = threading.Lock()

# Initialize DBA Agent instance
agent_instance = DBAAgent()


def verify_bearer_token(authorization: Optional[str] = Header(None)) -> bool:
    """Verifies Bearer token against AGENT_API_KEY using hmac.compare_digest."""
    expected_token = os.getenv("AGENT_API_KEY", "").strip()
    if not expected_token:
        return True

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header. Expected Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected 'Bearer <token>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    client_token = parts[1].strip()
    if not hmac.compare_digest(client_token, expected_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True


# ==============================================================================
# PYDANTIC SCHEMAS
# ==============================================================================

class HealthResponse(BaseModel):
    status: str
    agent_id: str
    agent_role: str
    version: str
    timestamp: str
    llm_available: bool
    state: str


class AgentMetadata(BaseModel):
    agent_id: str
    agent_role: str
    version: str
    capabilities: List[str]
    supported_inputs: List[str]
    mandatory_outputs: List[str]
    description: str


class TaskRequest(BaseModel):
    task_id: Optional[str] = Field(default=None, description="Unique task identifier")
    type: Optional[str] = Field(default="DATABASE_DESIGN", description="Task type")
    requirements: Optional[str] = Field(default=None, description="Raw SRS text or requirements string")
    brief: Optional[str] = Field(default=None, description="Alternative alias for requirements")
    content: Optional[str] = Field(default=None, description="Alternative alias for requirements text")
    file_path: Optional[str] = Field(default=None, description="Relative or absolute path to SRS file")


class ArtifactItem(BaseModel):
    id: str
    filename: str
    path: str
    checksum: str
    size_bytes: int


class TaskResponse(BaseModel):
    task_id: str
    status: str
    agent_id: str
    agent_role: str
    domain_name: str
    validation: Dict[str, Any]
    artifacts: List[ArtifactItem]
    summary: Dict[str, Any]
    completed_at: str


class ArtifactInboxRequest(BaseModel):
    artifact_id: str
    type: str
    created_by: str
    content: str
    checksum: Optional[str] = None


class GenerateFromSRSRequest(BaseModel):
    srs_content: Optional[str] = Field(None, description="Direct SRS content string")
    artifact_name: Optional[str] = Field("SRS.md", description="Artifact name in workspace or inbox to analyze")


# ==============================================================================
# API ENDPOINTS
# ==============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
def get_health() -> HealthResponse:
    """Public health check endpoint (no authentication required)."""
    return HealthResponse(
        status="OK",
        agent_id=AGENT_ID,
        agent_role=AGENT_ROLE,
        version="1.1.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
        llm_available=agent_instance.llm.is_available,
        state=AGENT_STATE["status"],
    )


@app.get("/status", tags=["Monitoring"])
def get_status(_: bool = Depends(verify_bearer_token)) -> Dict[str, Any]:
    """Returns agent operational status, metrics, and health."""
    with STATE_LOCK:
        artifacts_count = len(list(agent_instance.artifact_dir.glob("*")))
        return {
            "status": "healthy",
            "agent_id": AGENT_ID,
            "role": AGENT_ROLE,
            "state": AGENT_STATE["status"],
            "current_task_id": AGENT_STATE["current_task_id"],
            "llm_available": agent_instance.llm.is_available,
            "artifacts_count": artifacts_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


@app.get("/agent", response_model=AgentMetadata, tags=["Metadata"])
def get_agent(_: bool = Depends(verify_bearer_token)) -> AgentMetadata:
    """Returns agent capabilities and metadata (requires Bearer token)."""
    return AgentMetadata(
        agent_id=AGENT_ID,
        agent_role=AGENT_ROLE,
        version="1.1.0",
        capabilities=[
            "SRS Requirements Analysis",
            "Entity & Domain Modeling",
            "Primary Key & Foreign Key Architecture",
            "Mermaid ERD Generation",
            "3NF Normalization & Intentional Denormalization Justification",
            "ANSI SQL & PostgreSQL DDL Schema Compilation",
            "SQL Syntax & In-Memory SQLite Execution Validation",
            "Comprehensive Indexing Strategy (B-Tree, Partial, Composite, GIN)",
            "Query Optimization & Anti-Pattern Analysis",
            "Bidirectional SRS Traceability Verification",
        ],
        supported_inputs=["REQUIREMENTS.md", "SRS text", "Domain brief", "POST /tasks payload"],
        mandatory_outputs=[
            "DATA_REQUIREMENTS.md",
            "ERD.md",
            "DATABASE_DESIGN.md",
            "schema.sql",
            "INDEX_STRATEGY.md",
            "DATABASE_REVIEW.md",
        ],
        description="Senior Database Administrator and Architect AI Agent delivering production-ready relational schemas.",
    )


@app.get("/state", tags=["Monitoring"])
def get_state(_: bool = Depends(verify_bearer_token)) -> Dict[str, Any]:
    """Returns current agent execution state."""
    with STATE_LOCK:
        return {
            "agent_id": AGENT_ID,
            "status": AGENT_STATE["status"],
            "current_task_id": AGENT_STATE["current_task_id"],
        }


@app.post("/tasks", response_model=TaskResponse, tags=["Task Execution"])
def create_task(payload: TaskRequest, _: bool = Depends(verify_bearer_token)) -> TaskResponse:
    """Executes database design pipeline on input requirements."""
    # Concurrency lock check
    with STATE_LOCK:
        if AGENT_STATE["status"] == "BUSY":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Agent is busy executing task '{AGENT_STATE['current_task_id']}'.",
            )
        task_id = payload.task_id or f"task_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        AGENT_STATE["status"] = "BUSY"
        AGENT_STATE["current_task_id"] = task_id

    try:
        # Determine input content
        input_text = payload.requirements or payload.brief or payload.content or ""
        if not input_text and payload.file_path:
            p = Path(payload.file_path)
            if not p.is_absolute():
                p = agent_instance.workspace_dir / payload.file_path
            if p.is_file():
                input_text = p.read_text(encoding="utf-8")
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Specified file_path not found: {payload.file_path}",
                )

        if not input_text:
            # Check for received SRS in workspace
            inbox_srs = agent_instance.workspace_dir / "SRS.md"
            if inbox_srs.is_file():
                input_text = inbox_srs.read_text(encoding="utf-8")
                logger.info(f"Loaded SRS from inbox workspace ({len(input_text)} characters).")

        if not input_text:
            # Fallback to checking default brief in workspace
            sample_brief = agent_instance.workspace_dir / "sample_ba_srs.md"
            if sample_brief.is_file():
                input_text = sample_brief.read_text(encoding="utf-8")
            else:
                input_text = "Project: E-Commerce Store with user auth, product catalog, orders, and payments."

        logger.info(f"Executing database design workflow for task [{task_id}]...")
        result = agent_instance.run(input_text)

        response = TaskResponse(
            task_id=task_id,
            status=result["status"],
            agent_id=AGENT_ID,
            agent_role=AGENT_ROLE,
            domain_name=result["domain_name"],
            validation=result["validation"],
            artifacts=[ArtifactItem(**item) for item in result["artifacts"]],
            summary=result["summary"],
            completed_at=datetime.now(timezone.utc).isoformat(),
        )
        return response

    except Exception as exc:
        logger.error("Task execution failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database design pipeline execution failed: {str(exc)}",
        )
    finally:
        with STATE_LOCK:
            AGENT_STATE["status"] = "IDLE"
            AGENT_STATE["current_task_id"] = None


@app.post("/schema/generate-from-srs", tags=["Schema Generation"])
def generate_from_srs(payload: GenerateFromSRSRequest, _: bool = Depends(verify_bearer_token)) -> Dict[str, Any]:
    """Generates database schema and DDL SQL directly from received SRS document."""
    srs_text = payload.srs_content
    if not srs_text:
        target_path = agent_instance.workspace_dir / Path(payload.artifact_name or "SRS.md").name
        if target_path.is_file():
            srs_text = target_path.read_text(encoding="utf-8")
        else:
            inbox_path = agent_instance.artifact_dir / "inbox" / Path(payload.artifact_name or "SRS.md").name
            if inbox_path.is_file():
                srs_text = inbox_path.read_text(encoding="utf-8")

    if not srs_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No SRS content provided or found in workspace/inbox for '{payload.artifact_name}'.",
        )

    task_payload = TaskRequest(
        task_id=f"schema-srs-{int(time.time())}",
        requirements=srs_text,
    )
    task_res = create_task(task_payload, _)

    # Read generated SQL schema content
    schema_sql_path = agent_instance.artifact_dir / "schema.sql"
    sql_ddl = schema_sql_path.read_text(encoding="utf-8") if schema_sql_path.is_file() else ""

    return {
        "status": "SUCCESS",
        "domain_name": task_res.domain_name,
        "validation_passed": task_res.validation.get("all_passed", False),
        "tables_count": task_res.summary.get("total_tables", 0),
        "artifacts": [item.model_dump() for item in task_res.artifacts],
        "schema_sql": sql_ddl,
    }


@app.get("/artifacts", tags=["Artifact Management"])
def list_artifacts(_: bool = Depends(verify_bearer_token)) -> List[Dict[str, Any]]:
    """Lists all artifacts currently present in the artifacts directory."""
    artifacts = []
    for file_path in agent_instance.artifact_dir.glob("*"):
        if file_path.is_file() and not file_path.name.startswith("."):
            content = file_path.read_bytes()
            artifacts.append({
                "id": file_path.name,
                "filename": file_path.name,
                "size_bytes": len(content),
                "checksum": hashlib.sha256(content).hexdigest(),
                "modified_at": datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc).isoformat(),
            })
    return sorted(artifacts, key=lambda x: x["filename"])


@app.get("/artifacts/{artifact_id}/content", tags=["Artifact Management"])
def get_artifact_content(artifact_id: str, _: bool = Depends(verify_bearer_token)) -> Response:
    """Downloads or retrieves the raw content of an artifact file."""
    clean_id = Path(artifact_id).name
    target_file = agent_instance.artifact_dir / clean_id

    if not target_file.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact '{artifact_id}' not found.",
        )

    content = target_file.read_bytes()
    checksum = hashlib.sha256(content).hexdigest()

    media_type = "text/plain; charset=utf-8"
    if clean_id.endswith(".sql"):
        media_type = "application/sql; charset=utf-8"
    elif clean_id.endswith(".md"):
        media_type = "text/markdown; charset=utf-8"
    elif clean_id.endswith(".json"):
        media_type = "application/json; charset=utf-8"

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "X-Checksum-SHA256": checksum,
            "Content-Disposition": f'inline; filename="{clean_id}"',
        },
    )


@app.post("/artifacts/inbox", tags=["Artifact Management"])
def receive_artifact_inbox(payload: ArtifactInboxRequest, _: bool = Depends(verify_bearer_token)) -> Dict[str, Any]:
    """Receives an artifact pushed from another agent (e.g. BA Agent via HTTP API)."""
    computed_checksum = hashlib.sha256(payload.content.encode("utf-8")).hexdigest()
    if payload.checksum and payload.checksum != computed_checksum:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Checksum mismatch! Expected: {payload.checksum}, Computed: {computed_checksum}",
        )

    clean_filename = Path(payload.artifact_id).name
    save_path = agent_instance.workspace_dir / clean_filename
    save_path.write_text(payload.content, encoding="utf-8")

    # Also save copy in artifacts/inbox for audit trail
    inbox_dir = agent_instance.artifact_dir / "inbox"
    inbox_dir.mkdir(parents=True, exist_ok=True)
    (inbox_dir / clean_filename).write_text(payload.content, encoding="utf-8")

    logger.info(
        f"Artifact inbox received '{clean_filename}' from {payload.created_by} ({len(payload.content)} bytes, checksum: {computed_checksum[:8]}...)."
    )

    return {
        "status": "ACCEPTED",
        "saved_path": str(save_path),
        "checksum": computed_checksum,
        "bytes_written": len(payload.content.encode("utf-8")),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("agents.dba.api:app", host=HOST, port=PORT, reload=False)
