"""User Story & Gherkin Acceptance Criteria Generator Tool for BA AI Agent.

Generates INVEST-compliant User Stories and formal Gherkin Acceptance Criteria
for consumption by Product Owner, Developers, and QA Testers.
Produces USER_STORIES.md and ACCEPTANCE_CRITERIA.md.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .llm_client import GeminiClient
from .requirement_analyzer import RequirementItem

logger = logging.getLogger("ba_agent.user_story_generator")


@dataclass
class AcceptanceScenario:
    scenario_id: str
    title: str
    scenario_type: str  # Happy Path | Negative Case | Edge Case / Boundary
    given_clauses: List[str]
    when_clauses: List[str]
    then_clauses: List[str]
    tags: List[str] = field(default_factory=list)


@dataclass
class UserStory:
    id: str
    title: str
    role: str
    want: str
    so_that: str
    epic: str
    priority: str  # Critical | High | Medium | Low
    story_points: int  # 1, 2, 3, 5, 8, 13
    acceptance_criteria: List[AcceptanceScenario] = field(default_factory=list)
    notes_for_dev_sa: str = ""


@dataclass
class UserStorySet:
    project_name: str
    stories: List[UserStory] = field(default_factory=list)


class UserStoryGenerator:
    """Generates Agile User Stories and Gherkin Acceptance Criteria."""

    def __init__(self, llm_client: Optional[GeminiClient] = None) -> None:
        self.llm = llm_client or GeminiClient()

    def generate(
        self,
        requirements: List[RequirementItem],
        project_name: str = "Enterprise Software System",
        actors: Optional[List[str]] = None,
    ) -> UserStorySet:
        """Generate User Stories and Gherkin criteria from functional requirements."""
        actors = actors or ["End User", "System Administrator"]

        if self.llm.is_available:
            llm_result = self._generate_with_gemini(requirements, project_name, actors)
            if llm_result and llm_result.stories:
                return llm_result

        return self._generate_heuristic(requirements, project_name, actors)

    def _generate_with_gemini(
        self,
        requirements: List[RequirementItem],
        project_name: str,
        actors: List[str],
    ) -> Optional[UserStorySet]:
        """Use Gemini to produce INVEST user stories and Gherkin scenarios."""
        req_summary = "\n".join(
            [f"- [{r.id}] {r.title}: {r.description} (Priority: {r.priority})" for r in requirements]
        )

        system_prompt = (
            "You are a Senior Business Analyst (ba-01). Transform functional requirements into Agile User Stories.\n"
            "STRICT RULES:\n"
            "1. INVEST criteria: Independent, Negotiable, Valuable, Estimable, Small, Testable.\n"
            "2. Format: As a <role>, I want <want>, So that <so_that>.\n"
            "3. Every User Story must include at least 2 Acceptance Criteria in strict Gherkin syntax (Given / When / Then):\n"
            "   - One Happy Path scenario.\n"
            "   - One Negative or Edge Case scenario.\n"
            "4. NO code snippets, NO database schemas.\n"
            "Return JSON matching:\n"
            "{\n"
            '  "stories": [\n'
            "    {\n"
            '      "id": "US-001",\n'
            '      "title": "...",\n'
            '      "role": "...",\n'
            '      "want": "...",\n'
            '      "so_that": "...",\n'
            '      "epic": "...",\n'
            '      "priority": "High",\n'
            '      "story_points": 3,\n'
            '      "notes_for_dev_sa": "...",\n'
            '      "acceptance_criteria": [\n'
            "        {\n"
            '          "scenario_id": "SCN-001",\n'
            '          "title": "Successful execution",\n'
            '          "scenario_type": "Happy Path",\n'
            '          "tags": ["@smoke", "@critical"],\n'
            '          "given_clauses": ["the user is authenticated and on the page"],\n'
            '          "when_clauses": ["the user submits valid parameters"],\n'
            '          "then_clauses": ["the system processes the request and displays success"]\n'
            "        }\n"
            "      ]\n"
            "    }\n"
            "  ]\n"
            "}"
        )

        prompt = (
            f"Project: {project_name}\n"
            f"Identified Actors: {', '.join(actors)}\n"
            f"Functional Requirements:\n{req_summary}"
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
            story_objs = []
            for s in data.get("stories", []):
                crit_objs = []
                for c in s.get("acceptance_criteria", []):
                    crit_objs.append(
                        AcceptanceScenario(
                            scenario_id=c.get("scenario_id", "SCN-001"),
                            title=c.get("title", "Scenario Title"),
                            scenario_type=c.get("scenario_type", "Happy Path"),
                            given_clauses=c.get("given_clauses", []),
                            when_clauses=c.get("when_clauses", []),
                            then_clauses=c.get("then_clauses", []),
                            tags=c.get("tags", ["@regression"]),
                        )
                    )
                story_objs.append(
                    UserStory(
                        id=s.get("id", "US-001"),
                        title=s.get("title", "Feature Story"),
                        role=s.get("role", actors[0] if actors else "User"),
                        want=s.get("want", "access system capabilities"),
                        so_that=s.get("so_that", "achieve my operational goal"),
                        epic=s.get("epic", "Core Features"),
                        priority=s.get("priority", "High"),
                        story_points=int(s.get("story_points", 3)),
                        acceptance_criteria=crit_objs,
                        notes_for_dev_sa=s.get("notes_for_dev_sa", ""),
                    )
                )
            return UserStorySet(project_name=project_name, stories=story_objs)
        except Exception as exc:
            logger.warning("LLM story generation failed (%s); reverting to heuristic engine.", exc)
            return None

    def _generate_heuristic(
        self,
        requirements: List[RequirementItem],
        project_name: str,
        actors: List[str],
    ) -> UserStorySet:
        """Deterministic rule-based INVEST user story & Gherkin generation."""
        stories: List[UserStory] = []
        primary_actor = actors[0] if actors else "User"

        for idx, fr in enumerate(requirements, start=1):
            us_id = f"US-{idx:03d}"
            role = primary_actor
            if "admin" in fr.title.lower() or "quản lý" in fr.title.lower():
                role = "System Administrator"

            want_text = f"access and use the feature to {fr.description.lower().rstrip('.')}"
            so_that_text = f"I can fulfill the business requirement outlined in [{fr.id}] without errors"

            # Create Gherkin scenarios: Happy Path & Negative Case
            scenarios = [
                AcceptanceScenario(
                    scenario_id=f"{us_id}-AC-01",
                    title=f"Successfully execute {fr.title}",
                    scenario_type="Happy Path",
                    given_clauses=[
                        f"the actor is logged in as a valid '{role}'",
                        "all prerequisite state and permissions are active",
                    ],
                    when_clauses=[
                        f"the actor initiates '{fr.title}' with valid inputs",
                        "submits the operational request",
                    ],
                    then_clauses=[
                        "the system validates all business rules successfully",
                        f"the system executes the transaction and updates system state according to [{fr.id}]",
                        "the system displays an informative success confirmation message",
                    ],
                    tags=["@smoke", "@critical", "@happy-path"],
                ),
                AcceptanceScenario(
                    scenario_id=f"{us_id}-AC-02",
                    title=f"Reject execution of {fr.title} when inputs are invalid",
                    scenario_type="Negative Case",
                    given_clauses=[
                        f"the actor is logged in as a valid '{role}'",
                        "the actor is on the feature interface",
                    ],
                    when_clauses=[
                        "the actor submits incomplete, malformed, or empty mandatory parameters",
                    ],
                    then_clauses=[
                        "the system halts transaction processing immediately",
                        "no database state changes or mutations are committed",
                        "the system displays localized, actionable field-level validation errors",
                    ],
                    tags=["@negative", "@validation"],
                ),
                AcceptanceScenario(
                    scenario_id=f"{us_id}-AC-03",
                    title=f"Boundary condition for {fr.title}",
                    scenario_type="Edge Case",
                    given_clauses=[
                        f"the actor is interacting with '{fr.title}'",
                    ],
                    when_clauses=[
                        "the payload size or concurrency reaches extreme boundary limits",
                    ],
                    then_clauses=[
                        "the system safely handles the boundary condition without crashing",
                        "an appropriate status response or rate-limiting message is presented",
                    ],
                    tags=["@edge-case", "@regression"],
                ),
            ]

            story_points = 3 if fr.priority == "Must Have" else 2
            stories.append(
                UserStory(
                    id=us_id,
                    title=fr.title,
                    role=role,
                    want=want_text,
                    so_that=so_that_text,
                    epic="Core Operations" if idx <= 3 else "Extended Management",
                    priority="High" if fr.priority == "Must Have" else "Medium",
                    story_points=story_points,
                    acceptance_criteria=scenarios,
                    notes_for_dev_sa=f"Traceable to [{fr.id}]. Implement robust server-side validation and audit logging.",
                )
            )

        return UserStorySet(project_name=project_name, stories=stories)

    def generate_user_stories_doc(self, story_set: UserStorySet) -> str:
        """Generate formatted USER_STORIES.md markdown document."""
        doc = [
            f"# AGILE USER STORIES - {story_set.project_name.upper()}",
            "",
            "> **Agent ID**: `ba-01` | **Methodology**: Scrum / Agile INVEST Standard",
            "",
            "---",
            "",
            "## 1. INVEST Evaluation Principles",
            "- **Independent**: Stories can be developed and delivered autonomously without tight blocking coupling.",
            "- **Negotiable**: Business value is clear while technical implementation details are flexible for Dev/SA.",
            "- **Valuable**: Every story delivers tangible functional value to an identifiable user persona.",
            "- **Estimable**: Sized with Fibonacci story points (1, 2, 3, 5, 8, 13) for sprint planning.",
            "- **Small**: Scoped to fit comfortably within a single iterative sprint.",
            "- **Testable**: Accompanied by strict Gherkin acceptance criteria.",
            "",
            "## 2. User Stories Catalog",
            "",
            "| Story ID | Epic | Title | As a (Role) | Priority | Story Points |",
            "|:---|:---|:---|:---|:---:|:---:|",
        ]

        for s in story_set.stories:
            doc.append(f"| `{s.id}` | {s.epic} | **{s.title}** | `{s.role}` | `{s.priority}` | `{s.story_points} pts` |")

        doc.extend([
            "",
            "## 3. Detailed User Stories Specification",
        ])

        for s in story_set.stories:
            doc.extend([
                f"### {s.id}: {s.title}",
                f"- **Epic**: `{s.epic}`",
                f"- **Priority**: `{s.priority}` | **Estimation**: `{s.story_points} Story Points`",
                "",
                "> **User Story Statement**:",
                f"> **As a** `{s.role}`,  ",
                f"> **I want** {s.want},  ",
                f"> **So that** {s.so_that}.",
                "",
                f"**Implementation Notes for SA & Dev**: {s.notes_for_dev_sa}",
                "",
                "**Summary Acceptance Criteria Scenarios**:",
            ])
            for ac in s.acceptance_criteria:
                doc.append(f"- `[{ac.scenario_id}]` **{ac.title}** *({ac.scenario_type})* - Tags: `{', '.join(ac.tags)}`")
            doc.append("")

        doc.extend([
            "---",
            "*Document authored by Business Analyst Agent (`ba-01`). No programming code or DB schemas.*",
        ])

        return "\n".join(doc)

    def generate_acceptance_criteria_doc(self, story_set: UserStorySet) -> str:
        """Generate formatted ACCEPTANCE_CRITERIA.md document in Gherkin syntax."""
        doc = [
            f"# ACCEPTANCE CRITERIA SPECIFICATION - {story_set.project_name.upper()}",
            "",
            "> **Standard**: Gherkin / Cucumber BDD Specification  ",
            "> **Target Audience**: Quality Assurance / Tester (`tester-01`), Developers (`dev-01`)  ",
            "> **Author**: Business Analyst Agent (`ba-01`)",
            "",
            "---",
            "",
            "## 1. Overview & Verification Guidance",
            "This document establishes the official Behavior-Driven Development (BDD) test scenarios.",
            "Each scenario strictly adheres to `Given - When - Then` semantics to serve as direct inputs for automated testing suites.",
            "",
        ]

        for story in story_set.stories:
            doc.extend([
                f"## Feature: {story.title} (`{story.id}`)",
                f"  As a {story.role}",
                f"  I want {story.want}",
                f"  So that {story.so_that}",
                "",
            ])

            for scn in story.acceptance_criteria:
                tags_str = " ".join(scn.tags)
                doc.extend([
                    f"  {tags_str}",
                    f"  Scenario: [{scn.scenario_id}] {scn.title} ({scn.scenario_type})",
                ])

                for idx, g in enumerate(scn.given_clauses):
                    prefix = "Given" if idx == 0 else "And"
                    doc.append(f"    {prefix} {g}")

                for idx, w in enumerate(scn.when_clauses):
                    prefix = "When" if idx == 0 else "And"
                    doc.append(f"    {prefix} {w}")

                for idx, t in enumerate(scn.then_clauses):
                    prefix = "Then" if idx == 0 else "And"
                    doc.append(f"    {prefix} {t}")

                doc.append("")

        doc.extend([
            "---",
            "*Document generated by Business Analyst Agent (`ba-01`). Ready for automated ingestion by tester-01.*",
        ])

        return "\n".join(doc)
