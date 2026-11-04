"""Use Case & Business Process Generator Tool for BA AI Agent.

Generates formal UML Use Case specifications and Business Process workflow models
with role swimlanes and Mermaid diagrams.
Produces USE_CASES.md and BUSINESS_PROCESS.md.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .llm_client import GeminiClient
from .requirement_analyzer import RequirementItem

logger = logging.getLogger("ba_agent.usecase_generator")


@dataclass
class UseCaseStep:
    step_number: int
    actor_action: str
    system_response: str


@dataclass
class AlternativeFlow:
    flow_id: str
    branch_condition: str
    steps: List[str]


@dataclass
class ExceptionFlow:
    flow_id: str
    error_condition: str
    recovery_steps: List[str]


@dataclass
class UseCase:
    id: str
    title: str
    primary_actor: str
    secondary_actors: List[str]
    preconditions: List[str]
    trigger: str
    main_flow: List[UseCaseStep]
    alternative_flows: List[AlternativeFlow]
    exception_flows: List[ExceptionFlow]
    postconditions_success: str
    postconditions_failure: str
    related_fr: List[str] = field(default_factory=list)


@dataclass
class BusinessProcessModel:
    process_id: str
    process_name: str
    overview: str
    participants: List[str]
    swimlane_steps: List[Dict[str, str]]  # role, action, output
    business_rules_applied: List[str]
    mermaid_diagram: str


@dataclass
class UseCaseResult:
    project_name: str
    actors_catalog: List[Dict[str, str]]
    use_cases: List[UseCase] = field(default_factory=list)
    processes: List[BusinessProcessModel] = field(default_factory=list)


class UseCaseGenerator:
    """Generates formal Use Cases and Business Process specifications."""

    def __init__(self, llm_client: Optional[GeminiClient] = None) -> None:
        self.llm = llm_client or GeminiClient()

    def generate(
        self,
        requirements: List[RequirementItem],
        project_name: str = "Enterprise Software System",
        actors: Optional[List[str]] = None,
    ) -> UseCaseResult:
        """Generate Use Cases and Business Processes from requirements."""
        actors = actors or ["End User", "System Administrator"]

        if self.llm.is_available:
            llm_result = self._generate_with_gemini(requirements, project_name, actors)
            if llm_result and llm_result.use_cases:
                return llm_result

        return self._generate_heuristic(requirements, project_name, actors)

    def _generate_with_gemini(
        self,
        requirements: List[RequirementItem],
        project_name: str,
        actors: List[str],
    ) -> Optional[UseCaseResult]:
        """Use Gemini to generate formal Use Cases and Business Processes."""
        req_summary = "\n".join([f"- [{r.id}] {r.title}: {r.description}" for r in requirements])

        system_prompt = (
            "You are a Senior Business Analyst (ba-01). Generate formal Use Cases and Business Processes.\n"
            "STRICT RULES:\n"
            "1. Formal Use Cases must contain: Primary Actor, Preconditions, Trigger, Main Flow (numbered steps), Alternative Flows, Exception Flows, Postconditions.\n"
            "2. Business Process must include role swimlanes and a valid Mermaid flowchart TD diagram.\n"
            "3. NO code snippets, NO database schemas.\n"
            "Return JSON matching:\n"
            "{\n"
            '  "actors_catalog": [{"role": "...", "description": "..."}],\n'
            '  "use_cases": [\n'
            "    {\n"
            '      "id": "UC-001",\n'
            '      "title": "...",\n'
            '      "primary_actor": "...",\n'
            '      "secondary_actors": ["..."],\n'
            '      "preconditions": ["..."],\n'
            '      "trigger": "...",\n'
            '      "main_flow": [{"step_number": 1, "actor_action": "...", "system_response": "..."}],\n'
            '      "alternative_flows": [{"flow_id": "2a", "branch_condition": "...", "steps": ["..."]}],\n'
            '      "exception_flows": [{"flow_id": "3e", "error_condition": "...", "recovery_steps": ["..."]}],\n'
            '      "postconditions_success": "...",\n'
            '      "postconditions_failure": "...",\n'
            '      "related_fr": ["FR-001"]\n'
            "    }\n"
            "  ],\n"
            '  "processes": [\n'
            "    {\n"
            '      "process_id": "BP-001",\n'
            '      "process_name": "...",\n'
            '      "overview": "...",\n'
            '      "participants": ["..."],\n'
            '      "swimlane_steps": [{"role": "...", "action": "...", "output": "..."}],\n'
            '      "business_rules_applied": ["..."],\n'
            '      "mermaid_diagram": "flowchart TD\\n  A[Start] --> B[Process]\\n  B --> C[End]"\n'
            "    }\n"
            "  ]\n"
            "}"
        )

        prompt = (
            f"Project: {project_name}\n"
            f"Actors: {', '.join(actors)}\n"
            f"Requirements:\n{req_summary}"
        )

        try:
            response_text = self.llm.generate_text(prompt, system_instruction=system_prompt)
            if not response_text:
                return None

            cleaned_json = response_text.strip()
            if cleaned_json.startswith("```json"):
                cleaned_json = cleaned_json[7:]
            elif cleaned_json.startswith("```"):
                cleaned_json = cleaned_json[3:]
            if cleaned_json.endswith("```"):
                cleaned_json = cleaned_json[:-3]
            cleaned_json = cleaned_json.strip()

            data = json.loads(cleaned_json)

            uc_list = []
            for uc in data.get("use_cases", []):
                mf_steps = [UseCaseStep(**s) for s in uc.get("main_flow", [])]
                af_list = [AlternativeFlow(**a) for a in uc.get("alternative_flows", [])]
                ef_list = [ExceptionFlow(**e) for e in uc.get("exception_flows", [])]

                uc_list.append(
                    UseCase(
                        id=uc.get("id", "UC-001"),
                        title=uc.get("title", "Use Case"),
                        primary_actor=uc.get("primary_actor", actors[0]),
                        secondary_actors=uc.get("secondary_actors", []),
                        preconditions=uc.get("preconditions", []),
                        trigger=uc.get("trigger", "User requests operation"),
                        main_flow=mf_steps,
                        alternative_flows=af_list,
                        exception_flows=ef_list,
                        postconditions_success=uc.get("postconditions_success", "State updated"),
                        postconditions_failure=uc.get("postconditions_failure", "State preserved"),
                        related_fr=uc.get("related_fr", []),
                    )
                )

            bp_list = [BusinessProcessModel(**p) for p in data.get("processes", [])]

            return UseCaseResult(
                project_name=project_name,
                actors_catalog=data.get("actors_catalog", [{"role": a, "description": f"Actor {a}"} for a in actors]),
                use_cases=uc_list,
                processes=bp_list,
            )
        except Exception as exc:
            logger.warning("LLM usecase generation failed (%s); reverting to heuristic engine.", exc)
            return None

    def _generate_heuristic(
        self,
        requirements: List[RequirementItem],
        project_name: str,
        actors: List[str],
    ) -> UseCaseResult:
        """Deterministic rule-based Use Case & Business Process generation."""
        primary_actor = actors[0] if actors else "End User"
        admin_actor = "System Administrator"

        actors_catalog = [
            {"role": primary_actor, "description": f"Main operational stakeholder for {project_name}, initiating primary workflows."},
            {"role": admin_actor, "description": "Responsible for administrative governance, authorization, and system health oversight."},
            {"role": "External Service Provider", "description": "Third-party APIs (payment gateway, notification broker, external identity provider)."},
        ]

        use_cases: List[UseCase] = []

        for idx, fr in enumerate(requirements, start=1):
            uc_id = f"UC-{idx:03d}"
            actor = primary_actor
            if "admin" in fr.title.lower() or "quản lý" in fr.title.lower():
                actor = admin_actor

            main_flow = [
                UseCaseStep(
                    step_number=1,
                    actor_action=f"Actor navigates to the '{fr.title}' entry point.",
                    system_response="System verifies session authorization and presents the operational form with default parameters.",
                ),
                UseCaseStep(
                    step_number=2,
                    actor_action="Actor enters required business inputs and confirms submission.",
                    system_response="System performs synchronous schema validation on all submitted parameters.",
                ),
                UseCaseStep(
                    step_number=3,
                    actor_action="Actor reviews the operation summary.",
                    system_response=f"System applies business logic conforming to [{fr.id}], commits transaction, and logs audit record.",
                ),
                UseCaseStep(
                    step_number=4,
                    actor_action="Actor receives the completion confirmation.",
                    system_response="System displays updated status and provides reference transaction identifier.",
                ),
            ]

            alternative_flows = [
                AlternativeFlow(
                    flow_id="2a",
                    branch_condition="Actor chooses to cancel or save as draft before final confirmation.",
                    steps=[
                        "System prompts actor to confirm cancellation.",
                        "Actor confirms; system discards or saves uncommitted draft without state mutation.",
                        "System routes actor back to dashboard.",
                    ],
                )
            ]

            exception_flows = [
                ExceptionFlow(
                    flow_id="2b",
                    error_condition="Validation fails due to missing or invalid input attributes.",
                    recovery_steps=[
                        "System intercepts invalid submission before persistent execution.",
                        "System highlights offending input fields with contextual error messages.",
                        "System retains valid entered data; actor rectifies inputs and re-submits.",
                    ],
                ),
                ExceptionFlow(
                    flow_id="3a",
                    error_condition="Downstream integration or transaction lock timeout occurs.",
                    recovery_steps=[
                        "System triggers automatic transaction rollback.",
                        "System logs diagnostic alert for technical operations.",
                        "System presents retry guidance message to actor without exposing raw stack traces.",
                    ],
                ),
            ]

            use_cases.append(
                UseCase(
                    id=uc_id,
                    title=f"Execute {fr.title}",
                    primary_actor=actor,
                    secondary_actors=["External Service Provider"] if "payment" in fr.title.lower() else [],
                    preconditions=[
                        f"Actor is authenticated with valid credentials.",
                        f"Actor possesses active role permission for [{fr.id}].",
                    ],
                    trigger=f"Actor initiates {fr.title} from interface.",
                    main_flow=main_flow,
                    alternative_flows=alternative_flows,
                    exception_flows=exception_flows,
                    postconditions_success=f"Business operation for [{fr.id}] completed successfully and audited.",
                    postconditions_failure="System state remains unmutated; error recorded in operational logs.",
                    related_fr=[fr.id],
                )
            )

        # Build Business Process Model
        mermaid_diag = (
            "flowchart TD\n"
            f'  Start(["Start: Initiated by {primary_actor}"]) --> Step1["Step 1: Input Parameters & Form Submission"]\n'
            '  Step1 --> Validate{"Step 2: Server-side Validation"}\n'
            '  Validate -- "Invalid" --> HandleErr["Display Contextual Validation Errors"]\n'
            "  HandleErr --> Step1\n"
            '  Validate -- "Valid" --> Step3["Step 3: Execute Business Rules & Apply Logic"]\n'
            '  Step3 --> ExternalCheck{"External Integration Required?"}\n'
            '  ExternalCheck -- "Yes" --> CallExt["Call External Provider API"]\n'
            '  CallExt --> ExtResp{"Response OK?"}\n'
            '  ExtResp -- "No" --> Rollback["Execute Rollback & Error Log"]\n'
            '  Rollback --> FinishFail(["Failed State Notification"])\n'
            '  ExtResp -- "Yes" --> CommitState["Commit Business Transaction"]\n'
            '  ExternalCheck -- "No" --> CommitState\n'
            '  CommitState --> Audit["Log Immutable Audit Trail"]\n'
            '  Audit --> DispatchNotif["Dispatch Status Notification"]\n'
            f'  DispatchNotif --> Success(["End: Success Completed for {primary_actor}"])\n'
        )

        swimlane_steps = [
            {"role": primary_actor, "action": "Submits operation request via interface with business data", "output": "Encrypted HTTP Request"},
            {"role": "System Core API", "action": "Performs authentication, rate-limiting, and schema validation", "output": "Validated Domain Payload"},
            {"role": "Business Rule Engine", "action": "Executes domain integrity constraints and state transition", "output": "Domain Event"},
            {"role": admin_actor, "action": "Monitors aggregated transaction dashboard and handles escalations", "output": "Audit Review"},
        ]

        bp_model = BusinessProcessModel(
            process_id="BP-001",
            process_name=f"End-to-End Core Operations Workflow for {project_name}",
            overview=f"Comprehensive lifecycle workflow governing business transactions initiated by stakeholders in {project_name}.",
            participants=[primary_actor, admin_actor, "System Core API", "Business Rule Engine"],
            swimlane_steps=swimlane_steps,
            business_rules_applied=[
                "All transactions must be validated server-side prior to persistence.",
                "Atomic commit with full rollback upon external failure.",
                "Immutable audit logging for compliance.",
            ],
            mermaid_diagram=mermaid_diag,
        )

        return UseCaseResult(
            project_name=project_name,
            actors_catalog=actors_catalog,
            use_cases=use_cases,
            processes=[bp_model],
        )

    def generate_use_cases_doc(self, uc_result: UseCaseResult) -> str:
        """Generate formatted USE_CASES.md markdown document."""
        doc = [
            f"# USE CASES SPECIFICATION - {uc_result.project_name.upper()}",
            "",
            "> **Agent ID**: `ba-01` | **Methodology**: Formal UML Use Case Specification  ",
            "> **Standard**: Alistair Cockburn Formal Template",
            "",
            "---",
            "",
            "## 1. Actor Catalog",
            "",
            "| Actor Role | Classification | Description & Responsibilities |",
            "|:---|:---:|:---|",
        ]

        for a in uc_result.actors_catalog:
            classification = "Primary" if "User" in a["role"] or "Customer" in a["role"] else "Secondary / System"
            doc.append(f"| **{a['role']}** | `{classification}` | {a['description']} |")

        doc.extend([
            "",
            "## 2. Use Case Summary Matrix",
            "",
            "| Use Case ID | Use Case Name | Primary Actor | Tracing FR | Postcondition Success |",
            "|:---|:---|:---|:---:|:---|",
        ])

        for uc in uc_result.use_cases:
            fr_str = ", ".join(uc.related_fr) if uc.related_fr else "Core"
            doc.append(f"| `{uc.id}` | **{uc.title}** | `{uc.primary_actor}` | `{fr_str}` | {uc.postconditions_success} |")

        doc.extend([
            "",
            "## 3. Detailed Formal Use Cases",
        ])

        for uc in uc_result.use_cases:
            secondary_str = ", ".join(uc.secondary_actors) if uc.secondary_actors else "None"
            doc.extend([
                f"### {uc.id}: {uc.title}",
                f"- **Primary Actor**: `{uc.primary_actor}`",
                f"- **Secondary Actors**: `{secondary_str}`",
                f"- **Trigger**: {uc.trigger}",
                f"- **Tracing Requirements**: `{', '.join(uc.related_fr)}`",
                "",
                "#### Preconditions:",
            ])
            for pre in uc.preconditions:
                doc.append(f"- {pre}")

            doc.extend([
                "",
                "#### Main Success Scenario (Normal Flow):",
                "| Step | Actor Action | System Response |",
                "|:---:|:---|:---|",
            ])
            for s in uc.main_flow:
                doc.append(f"| {s.step_number} | {s.actor_action} | {s.system_response} |")

            doc.extend([
                "",
                "#### Alternative Flows:",
            ])
            if uc.alternative_flows:
                for af in uc.alternative_flows:
                    doc.append(f"- **Flow [{af.flow_id}]**: *{af.branch_condition}*")
                    for step in af.steps:
                        doc.append(f"  - {step}")
            else:
                doc.append("- No alternative branching flows specified.")

            doc.extend([
                "",
                "#### Exception / Failure Flows:",
            ])
            if uc.exception_flows:
                for ef in uc.exception_flows:
                    doc.append(f"- **Error [{ef.flow_id}]**: *{ef.error_condition}*")
                    for step in ef.recovery_steps:
                        doc.append(f"  - {step}")
            else:
                doc.append("- No unhandled exception flows specified.")

            doc.extend([
                "",
                "#### Postconditions:",
                f"- **Success Guarantee**: {uc.postconditions_success}",
                f"- **Minimal Guarantee (Failure)**: {uc.postconditions_failure}",
                "",
                "---",
            ])

        doc.append("*Authored by Business Analyst Agent (`ba-01`). Implementation details omitted by design.*")
        return "\n".join(doc)

    def generate_business_process_doc(self, uc_result: UseCaseResult) -> str:
        """Generate formatted BUSINESS_PROCESS.md markdown document."""
        doc = [
            f"# BUSINESS PROCESS & WORKFLOW MODEL - {uc_result.project_name.upper()}",
            "",
            "> **Standard**: BPMN / Workflow Modeling Standards  ",
            "> **Agent ID**: `ba-01` | **Role**: Business Analyst",
            "",
            "---",
            "",
            "## 1. Process Landscape Overview",
            "This document formalizes the operational workflows, cross-functional responsibilities, and decision logic.",
            "It guides the System Architect (`sa-01`) for orchestration design and Quality Assurance (`tester-01`) for end-to-end integration tests.",
            "",
        ]

        for p in uc_result.processes:
            doc.extend([
                f"## 2. Process Specification: {p.process_name} (`{p.process_id}`)",
                f"**Overview**: {p.overview}",
                "",
                "### 2.1 Process Participants & RACI Assignment",
                "",
                "| Participant Role | Swimlane Role | Interaction Scope |",
                "|:---|:---:|:---|",
            ])
            for part in p.participants:
                doc.append(f"| **{part}** | Core Participant | Initiates, executes, or audits process milestones |")

            doc.extend([
                "",
                "### 2.2 Swimlane Action Steps Matrix",
                "",
                "| Step # | Responsible Role | Action Performed | Expected Deliverable / Output |",
                "|:---:|:---|:---|:---|",
            ])
            for idx, s in enumerate(p.swimlane_steps, start=1):
                doc.append(f"| {idx} | **{s['role']}** | {s['action']} | `{s['output']}` |")

            doc.extend([
                "",
                "### 2.3 Enforced Business Rules",
            ])
            for br in p.business_rules_applied:
                doc.append(f"- **Rule**: {br}")

            doc.extend([
                "",
                "### 2.4 Visual Workflow Flowchart (Mermaid)",
                "```mermaid",
                p.mermaid_diagram,
                "```",
                "",
            ])

        doc.extend([
            "---",
            "*Document produced by Business Analyst Agent (`ba-01`). No code or database DDL.*",
        ])

        return "\n".join(doc)
