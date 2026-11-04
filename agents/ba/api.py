"""FastAPI REST API Service for BA AI Agent (ba-01).

Implements Multi-Agent System HTTP Agent API v1:
- GET  /health          Public health & heartbeat probe
- GET  /status          Agent operational status & state
- GET  /agent           Agent metadata, capabilities, and status
- POST /tasks           Execute business requirements analysis pipeline
- POST /srs/generate    Generate & export SRS specification document
- POST /srs/send-to-dba Transmit SRS artifact to DBA Agent via HTTP API
- GET  /artifacts       List generated specification artifacts
- GET  /artifacts/{id}  Read artifact content
- POST /artifacts/inbox Ingest incoming artifact from orchestrator
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .agent import BAAgent
from .logger import setup_logger

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "logs"
logger = setup_logger(agent_id="ba-01", log_dir=LOGS_DIR, log_filename="agent_ba.log")

app = FastAPI(
    title="BA AI Agent API (ba-01)",
    description="Business Analyst AI Agent service conforming to Multi-Agent System specification.",
    version="1.1.0",
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

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singleton Agent Instance
ba_agent = BAAgent()


# --- Security & Authentication ---
def verify_token(authorization: Optional[str] = Header(None)) -> bool:
    """Validate Bearer token against AGENT_API_KEY if configured."""
    expected_token = os.getenv("AGENT_API_KEY", "").strip()
    if not expected_token:
        return True

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Bearer authorization token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ", 1)[1].strip()
    if not hmac.compare_digest(token, expected_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Bearer authorization token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True


# --- Request & Response Models ---
class TaskRequest(BaseModel):
    task_id: Optional[str] = Field(None, description="Optional caller-defined task identifier")
    task_type: Optional[str] = Field("analyze_requirements", description="Type of task to perform")
    project_name: Optional[str] = Field("Software Application", description="Human-readable project title")
    description: Optional[str] = Field("", description="Raw requirement description / brief")
    requirements: Optional[str] = Field("", description="Alternative field for raw requirement text")
    prompt: Optional[str] = Field("", description="Alternative prompt field")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional project context")


class SRSGenerateRequest(BaseModel):
    project_name: str = Field("E-Commerce System", description="Name of the project")
    description: str = Field(..., description="High-level requirements or brief description")
    features: Optional[List[str]] = Field(default_factory=list, description="Key features list")
    domain: Optional[str] = Field("Retail / E-Commerce", description="Industry domain")


class SendToDBARequest(BaseModel):
    dba_endpoint: Optional[str] = Field(None, description="DBA Agent endpoint URL (defaults to DBA_ENDPOINT env)")
    dba_token: Optional[str] = Field(None, description="DBA Agent API Key (defaults to DBA_API_KEY env)")
    artifact_id: Optional[str] = Field("SRS.md", description="SRS artifact filename to send")
    srs_content: Optional[str] = Field(None, description="Direct SRS content (if omitted, reads from generated artifact)")
    trigger_schema_generation: bool = Field(True, description="Automatically trigger DBA schema generation after inbox acceptance")


class HealthResponse(BaseModel):
    status: str
    agent_id: str
    role: str
    version: str
    timestamp: str
    uptime_seconds: int


class InboxUploadRequest(BaseModel):
    filename: str
    content: str
    source_agent: Optional[str] = "pm-01"
    artifact_type: Optional[str] = "BRIEF"


# --- API Endpoints ---

@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
def get_health() -> HealthResponse:
    """Public health & heartbeat probe. No authentication required."""
    info = ba_agent.get_info()
    return HealthResponse(
        status="healthy",
        agent_id=info["agent_id"],
        role=info["role"],
        version=info["version"],
        timestamp=datetime.now(timezone.utc).isoformat(),
        uptime_seconds=info["uptime_seconds"],
    )


@app.get("/status", tags=["Monitoring"])
def get_status(_auth: bool = Depends(verify_token)) -> Dict[str, Any]:
    """Retrieve operational status, current state (IDLE/BUSY), and metrics."""
    info = ba_agent.get_info()
    artifacts = ba_agent.list_artifacts()
    return {
        "status": "healthy",
        "agent_id": info["agent_id"],
        "role": info["role"],
        "state": info["status"].upper(),
        "current_task_id": info["current_task_id"],
        "uptime_seconds": info["uptime_seconds"],
        "tasks_completed": info["tasks_completed"],
        "artifacts_count": len(artifacts),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/agent", tags=["Metadata"])
def get_agent_info(_auth: bool = Depends(verify_token)) -> Dict[str, Any]:
    """Retrieve full agent operational identity, capabilities, and runtime status."""
    return ba_agent.get_info()


@app.post("/tasks", status_code=status.HTTP_200_OK, tags=["Task Execution"])
def create_task(payload: TaskRequest, _auth: bool = Depends(verify_token)) -> Dict[str, Any]:
    """Execute business requirements analysis task and produce the 6 specification documents.

    Returns HTTP 409 Conflict if the agent is already executing a task.
    """
    task_dict = payload.model_dump()
    text_content = (
        task_dict.get("description")
        or task_dict.get("requirements")
        or task_dict.get("prompt")
        or ""
    )
    task_dict["description"] = text_content

    try:
        logger.info(f"Task initiated: '{task_dict.get('project_name')}'")
        result = ba_agent.execute_task(task_dict)
        return result
    except RuntimeError as busy_err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(busy_err),
        )
    except Exception as exc:
        logger.error("Error executing task: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Task processing failed: {exc}",
        )


@app.post("/srs/generate", status_code=status.HTTP_200_OK, tags=["SRS Management"])
def generate_srs(payload: SRSGenerateRequest, _auth: bool = Depends(verify_token)) -> Dict[str, Any]:
    """Generate and export the Software Requirements Specification (SRS) artifact."""
    task_payload = {
        "project_name": payload.project_name,
        "description": payload.description,
        "context": {
            "domain": payload.domain,
            "features": payload.features,
        },
    }

    try:
        logger.info(f"Generating SRS for project: '{payload.project_name}'")
        result = ba_agent.execute_task(task_payload)
        srs_content = ba_agent.get_artifact_content("SRS.md") or ""
        checksum = hashlib.sha256(srs_content.encode("utf-8")).hexdigest()

        return {
            "status": "SUCCESS",
            "project_name": payload.project_name,
            "artifact_id": "SRS.md",
            "checksum": checksum,
            "size_bytes": len(srs_content.encode("utf-8")),
            "srs_content": srs_content,
            "summary": result.get("summary", {}),
            "artifacts_generated": result.get("artifacts", []),
        }
    except Exception as exc:
        logger.error("SRS generation failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate SRS: {exc}",
        )


@app.post("/srs/send-to-dba", tags=["Cross-Agent Communication"])
async def send_srs_to_dba(
    payload: SendToDBARequest,
    _auth: bool = Depends(verify_token),
) -> Dict[str, Any]:
    """Send SRS document over HTTP API to DBA Agent inbox (Zero shared folder architecture)."""
    dba_endpoint = (
        payload.dba_endpoint
        or os.getenv("DBA_ENDPOINT", "http://127.0.0.1:8004")
    ).rstrip("/")
    dba_token = payload.dba_token or os.getenv("DBA_API_KEY", "")

    # Retrieve SRS content
    srs_content = payload.srs_content
    if not srs_content:
        srs_content = ba_agent.get_artifact_content(payload.artifact_id or "SRS.md")

    if not srs_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"SRS content not found in artifact '{payload.artifact_id}'. Please generate SRS first.",
        )

    checksum = hashlib.sha256(srs_content.encode("utf-8")).hexdigest()

    headers = {}
    if dba_token:
        headers["Authorization"] = f"Bearer {dba_token}"

    inbox_payload = {
        "artifact_id": payload.artifact_id or "SRS.md",
        "type": "SRS_DOCUMENT",
        "created_by": "ba-01",
        "content": srs_content,
        "checksum": checksum,
    }

    logger.info(f"Sending SRS ({len(srs_content)} bytes) to DBA Agent at {dba_endpoint}/artifacts/inbox")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            inbox_resp = await client.post(
                f"{dba_endpoint}/artifacts/inbox",
                json=inbox_payload,
                headers=headers,
            )
            if inbox_resp.status_code not in (200, 201):
                logger.error(f"DBA inbox returned status {inbox_resp.status_code}: {inbox_resp.text}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"DBA Agent inbox rejected artifact with HTTP {inbox_resp.status_code}: {inbox_resp.text}",
                )
            inbox_data = inbox_resp.json()
        except httpx.RequestError as exc:
            logger.error(f"Failed to connect to DBA Agent at {dba_endpoint}: {exc}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Cannot connect to DBA Agent at {dba_endpoint}: {exc}",
            )

        dba_task_result = None
        if payload.trigger_schema_generation:
            logger.info("Triggering DBA schema generation pipeline...")
            task_payload = {
                "type": "DATABASE_DESIGN",
                "requirements": srs_content,
                "task_id": f"dba-task-{int(time.time())}",
            }
            try:
                task_resp = await client.post(
                    f"{dba_endpoint}/tasks",
                    json=task_payload,
                    headers=headers,
                )
                if task_resp.status_code == 200:
                    dba_task_result = task_resp.json()
                    logger.info("DBA schema generation completed successfully!")
                else:
                    logger.warning(f"DBA task endpoint returned HTTP {task_resp.status_code}")
            except Exception as exc:
                logger.error(f"Error triggering DBA schema task: {exc}")

    return {
        "status": "SENT_SUCCESSFULLY",
        "dba_endpoint": dba_endpoint,
        "artifact_id": payload.artifact_id or "SRS.md",
        "checksum": checksum,
        "dba_inbox_response": inbox_data,
        "dba_task_result": dba_task_result,
    }


@app.get("/artifacts", tags=["Artifact Management"])
def list_artifacts(_auth: bool = Depends(verify_token)) -> Dict[str, Any]:
    """List all specification artifacts generated by the BA agent."""
    artifacts = ba_agent.list_artifacts()
    return {
        "agent_id": ba_agent.agent_id,
        "count": len(artifacts),
        "artifacts": artifacts,
    }


@app.get("/artifacts/{filename}", tags=["Artifact Management"])
def get_artifact(filename: str, _auth: bool = Depends(verify_token)) -> Response:
    """Retrieve content of a specific artifact file."""
    content = ba_agent.get_artifact_content(filename)
    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact '{filename}' not found.",
        )
    return Response(
        content=content,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@app.post("/artifacts/inbox", status_code=status.HTTP_201_CREATED, tags=["Artifact Management"])
def upload_inbox_artifact(payload: InboxUploadRequest, _auth: bool = Depends(verify_token)) -> Dict[str, Any]:
    """Accept incoming artifact (e.g. project brief from PM Conductor) into workspace."""
    safe_name = Path(payload.filename).name
    target_path = ba_agent.workspace_dir / safe_name
    content_bytes = payload.content.encode("utf-8")
    target_path.write_bytes(content_bytes)

    checksum = hashlib.sha256(content_bytes).hexdigest()
    logger.info("Received inbox artifact %s from %s", safe_name, payload.source_agent)

    return {
        "status": "received",
        "filename": safe_name,
        "saved_path": str(target_path.resolve()),
        "size_bytes": len(content_bytes),
        "checksum": checksum,
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8003"))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("agents.ba.api:app", host=host, port=port, reload=False)
