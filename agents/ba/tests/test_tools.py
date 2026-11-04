"""Unit tests for BA Agent tools."""

import pytest
from agents.ba.tools.requirement_analyzer import RequirementAnalyzer, RequirementItem
from agents.ba.tools.user_story_generator import UserStoryGenerator
from agents.ba.tools.usecase_generator import UseCaseGenerator


SAMPLE_BRIEF = """
Hệ thống Thương mại Điện tử E-Shop:
- Cho phép khách hàng đăng ký, đăng nhập tài khoản.
- Tìm kiếm sản phẩm theo danh mục và từ khóa.
- Thêm sản phẩm vào giỏ hàng và đặt hàng.
- Thanh toán đơn hàng trực tuyến qua cổng thanh toán.
- Quản trị viên xem báo cáo doanh thu và quản lý danh mục sản phẩm.
- Hệ thống cần phản hồi nhanh dưới 1 giây và chịu tải 2000 người dùng đồng thời.
"""


def test_requirement_analyzer_heuristic():
    analyzer = RequirementAnalyzer()
    result = analyzer.analyze(SAMPLE_BRIEF, project_name="E-Shop Platform")

    assert result.project_name == "E-Shop Platform"
    assert len(result.functional_requirements) >= 3
    assert len(result.non_functional_requirements) >= 3
    assert len(result.assumptions) >= 1
    assert len(result.clarification_questions) >= 1
    assert "Customer" in result.actors or "End User" in result.actors

    # Verify generated markdown documents
    req_doc = analyzer.generate_requirements_doc(result)
    assert "# BUSINESS REQUIREMENTS DOCUMENT" in req_doc
    assert "Functional Requirements (FR) Matrix" in req_doc
    assert "Non-Functional Requirements (NFR) Matrix" in req_doc
    assert "Assumptions Register" in req_doc
    assert "Clarification Questions" in req_doc

    srs_doc = analyzer.generate_srs_doc(result)
    assert "# SOFTWARE REQUIREMENTS SPECIFICATION (SRS)" in srs_doc
    assert "IEEE 830" in srs_doc
    assert "External Interface Requirements" in srs_doc


def test_user_story_generator():
    reqs = [
        RequirementItem(id="FR-001", title="Đăng nhập tài khoản", description="Khách hàng đăng nhập vào hệ thống bằng email và mật khẩu", priority="Must Have"),
        RequirementItem(id="FR-002", title="Đặt hàng trực tuyến", description="Khách hàng tạo đơn hàng từ giỏ hàng", priority="Must Have"),
        RequirementItem(id="FR-003", title="Quản lý sản phẩm", description="Quản trị viên thêm và sửa thông tin sản phẩm", priority="Should Have"),
    ]

    generator = UserStoryGenerator()
    story_set = generator.generate(reqs, project_name="E-Shop Platform", actors=["Customer", "Administrator"])

    assert len(story_set.stories) == 3
    first_story = story_set.stories[0]
    assert first_story.id == "US-001"
    assert "Customer" in first_story.role or "User" in first_story.role
    assert len(first_story.acceptance_criteria) >= 2

    # Verify document generation
    us_doc = generator.generate_user_stories_doc(story_set)
    assert "# AGILE USER STORIES" in us_doc
    assert "As a" in us_doc
    assert "I want" in us_doc
    assert "So that" in us_doc

    ac_doc = generator.generate_acceptance_criteria_doc(story_set)
    assert "# ACCEPTANCE CRITERIA SPECIFICATION" in ac_doc
    assert "Feature:" in ac_doc
    assert "Scenario:" in ac_doc
    assert "Given" in ac_doc
    assert "When" in ac_doc
    assert "Then" in ac_doc


def test_usecase_generator():
    reqs = [
        RequirementItem(id="FR-001", title="Đặt hàng", description="Người dùng thực hiện đặt hàng", priority="Must Have"),
        RequirementItem(id="FR-002", title="Thanh toán trực tuyến", description="Thanh toán qua cổng ngân hàng", priority="Must Have"),
    ]

    generator = UseCaseGenerator()
    result = generator.generate(reqs, project_name="E-Shop Platform", actors=["Customer", "Administrator"])

    assert len(result.use_cases) == 2
    assert len(result.processes) >= 1

    first_uc = result.use_cases[0]
    assert first_uc.id == "UC-001"
    assert len(first_uc.main_flow) >= 3
    assert len(first_uc.alternative_flows) >= 1
    assert len(first_uc.exception_flows) >= 1

    uc_doc = generator.generate_use_cases_doc(result)
    assert "# USE CASES SPECIFICATION" in uc_doc
    assert "Main Success Scenario" in uc_doc
    assert "Alternative Flows" in uc_doc
    assert "Exception / Failure Flows" in uc_doc

    bp_doc = generator.generate_business_process_doc(result)
    assert "# BUSINESS PROCESS & WORKFLOW MODEL" in bp_doc
    assert "flowchart TD" in bp_doc
    assert "RACI" in bp_doc or "Swimlane" in bp_doc
