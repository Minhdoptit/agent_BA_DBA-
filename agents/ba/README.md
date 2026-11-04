# 🏛️ BA AI Agent (Business Analyst) - `ba-01`
### Professional Multi-Agent System Component | Agent Contract v1.1.0

Agent **Business Analyst (`ba-01`)** là thành viên chuyên trách kỹ nghệ yêu cầu phần mềm (Requirements Engineering) trong hệ thống đa tác tử (Multi-Agent System). Agent có nhiệm vụ tiếp nhận yêu cầu dự án phần mềm ở dạng thô từ Product Owner hoặc Stakeholder, phân tích miền nghiệp vụ, bóc tách yêu cầu chức năng / phi chức năng, phát hiện mâu thuẫn, xây dựng giả định rõ ràng và xuất ra **6 bộ tài liệu đặc tả chuẩn hóa** để bàn giao cho các Agent khác trong chuỗi phát triển phần mềm tự động.

---

## 📁 1. Cấu trúc thư mục

```text
agents/ba/
├── api.py                      # FastAPI REST API Service (Cổng giao tiếp chuẩn Agent API v1)
├── agent.py                    # BAAgent Orchestrator điều phối toàn bộ pipeline phân tích
├── prompts/
│   └── ba_system_prompt.md     # System Prompt chuẩn Senior Business Analyst
├── tools/
│   ├── __init__.py             # Export các công cụ phân tích
│   ├── llm_client.py           # Client kết nối Google Gemini API kèm fallback thông minh
│   ├── requirement_analyzer.py # Bóc tách FR (MoSCoW), NFR (ISO 25010), Assumptions, Gaps
│   ├── user_story_generator.py # Sinh User Stories (INVEST) và Acceptance Criteria (Gherkin)
│   └── usecase_generator.py    # Sinh formal Use Cases và mô hình Business Process (Mermaid)
├── workspace/                  # Thư mục lưu trữ tạm / tiếp nhận file đầu vào từ PM (Inbox)
├── artifacts/                  # Thư mục lưu trữ 6 tài liệu đặc tả đầu ra (Outbox)
├── tests/
│   ├── __init__.py
│   ├── test_tools.py           # Unit test cho 3 tools lõi
│   ├── test_agent.py           # Integration test cho BAAgent và cơ chế Concurrency Lock
│   ├── test_api.py             # Integration test cho các API endpoint và Bearer Auth
│   └── test_document_quality.py# Kiểm tra chất lượng và tính tuân thủ nguyên tắc BA
├── requirements.txt            # Danh sách thư viện phụ thuộc
├── .env.example                # File mẫu cấu hình biến môi trường
└── README.md                   # Tài liệu hướng dẫn sử dụng và triển khai
```

---

## 🎯 2. Năng lực cốt lõi (Capabilities)

1. **Phân tích yêu cầu nghiệp vụ chuyên sâu**: Elicitation, phân tích bài toán, xác định mục tiêu kinh doanh (Business Goals), phạm vi In-Scope và Out-of-Scope.
2. **Bóc tách Functional Requirements (FR)**: Định danh theo chuẩn `FR-001, FR-002...` kèm ưu tiên theo phương pháp **MoSCoW** (`Must Have`, `Should Have`, `Could Have`, `Won't Have`) và tiêu chí nghiệm thu sơ bộ.
3. **Phân tích Non-Functional Requirements (NFR)**: Phân loại theo chuẩn chất lượng **ISO/IEC 25010** (Performance, Security, Scalability, Reliability, Usability, Compliance) kèm chỉ số đo lường (SLA, latency target, throughput).
4. **Tạo Agile User Stories**: Tuân thủ nguyên tắc **INVEST** (Independent, Negotiable, Valuable, Estimable, Small, Testable) theo mẫu chuẩn `As a <Role>, I want <Feature>, So that <Business Benefit>`.
5. **Tạo Acceptance Criteria chuẩn Gherkin**: Khung kịch bản BDD (`Given - When - Then - And`) bao gồm cả Happy Path, Negative Case và Boundary/Edge Case cho QA Tester.
6. **Xây dựng Use Case chính quy (Formal Use Cases)**: Actor chính/phụ, điều kiện tiên quyết (Preconditions), tác nhân kích hoạt (Trigger), luồng sự kiện chính (Main Flow), luồng rẽ nhánh (Alternative Flows), luồng ngoại lệ (Exception Flows) và điều kiện sau (Postconditions).
7. **Mô hình hóa quy trình nghiệp vụ (Business Process Modeling)**: Ma trận trách nhiệm theo vai trò (Swimlanes / RACI) và sơ đồ luồng dữ liệu tự động vẽ bằng **Mermaid** (`graph TD` / `flowchart TD`).
8. **Phát hiện mâu thuẫn & thiếu sót (Gap & Conflict Detection)**: Tự động rà soát sự bất đồng bộ hoặc xung đột logic giữa các yêu cầu.
9. **Đưa ra giả định rõ ràng (`[ASSUMPTION-XXX]`)**: Khi yêu cầu đầu vào chưa rõ ràng, agent không tự đoán mò mà ghi rõ giả định, lý do và tác động.
10. **Câu hỏi làm rõ nghiệp vụ (`[Q-XXX]`)**: Soạn thảo các câu hỏi ưu tiên cao gửi lại PO/Stakeholder để chốt phạm vi.

---

## 📋 3. Sáu (6) tài liệu đầu ra chuẩn hóa (Output Artifacts)

Mỗi khi nhận tác vụ phân tích, BA Agent sẽ tạo ra đúng 6 file markdown có liên kết chặt chẽ trong thư mục `artifacts/`:

| Tên File | Tiêu chuẩn | Đối tượng tiếp nhận chính | Mục đích sử dụng |
|:---|:---:|:---:|:---|
| **`REQUIREMENTS.md`** | ISO/IEC 29148 | PO, PM, Tech Lead | Tổng quan phạm vi, ma trận FR (MoSCoW), NFR (ISO 25010), Business Rules, Assumptions, Conflicts và câu hỏi làm rõ. |
| **`SRS.md`** | IEEE 830-1998 | System Architect (`sa-01`) | Đặc tả kỹ thuật phần mềm đầy đủ, giao diện hệ thống, ràng buộc kiến trúc, ma trận truy vết yêu cầu (Traceability Matrix). |
| **`USER_STORIES.md`** | Agile INVEST | Dev (`dev-01`), PM (`pm-01`) | Danh mục User Story kèm độ ưu tiên, Story Points (Fibonacci) và ghi chú triển khai cho kỹ thuật. |
| **`USE_CASES.md`** | Cockburn Formal | QA Tester (`tester-01`), Dev | Đặc tả chi tiết từng Use Case với các luồng tương tác Main/Alternative/Exception flows. |
| **`ACCEPTANCE_CRITERIA.md`** | Gherkin / Cucumber | QA Tester (`tester-01`) | Bộ kịch bản BDD `Given-When-Then` có gắn tag `@smoke`, `@regression`, `@critical` phục vụ viết test tự động. |
| **`BUSINESS_PROCESS.md`** | BPMN Workflow | SA, Dev, Stakeholders | Mô hình hóa quy trình nghiệp vụ tổng thể, phân công Swimlane, sơ đồ Mermaid trực quan. |

---

## ⚖️ 4. Nguyên tắc hoạt động nghiêm ngặt (Guardrails)

- **Chỉ phân tích nghiệp vụ**: Tuyệt đối **KHÔNG** tự ý lập trình mã nguồn ứng dụng (backend/frontend).
- **Không thiết kế cơ sở dữ liệu**: Tuyệt đối **KHÔNG** tự ý tạo câu lệnh DDL (`CREATE TABLE`, `ALTER TABLE`, chỉ mục, khóa ngoại...). Đây là thẩm quyền của **DBA Agent (`dba-01`)**.
- **Tôn trọng ý chí người dùng**: Không tự ý sửa đổi hoặc lược bỏ yêu cầu cốt lõi của bài toán.
- **Minh bạch thông tin qua ASSUMPTION**: Bất kỳ thông số kỹ thuật hoặc quy tắc nào chưa được chỉ định rõ phải được đóng khung thành `[ASSUMPTION-XXX]`.
- **Khóa đơn nhiệm (Concurrency Lock)**: Mỗi thời điểm BA Agent chỉ thực thi 1 tác vụ duy nhất. Request đồng thời sẽ trả về `HTTP 409 Conflict`.

---

## ⚙️ 5. Cài đặt và cấu hình

### 5.1 Cài đặt môi trường

```powershell
# Chuyển vào thư mục agent BA
cd agents/ba

# Cài đặt các thư viện phụ thuộc
pip install -r requirements.txt
```

### 5.2 Thiết lập file cấu hình `.env`

Tạo file `.env` từ `.env.example`:

```properties
# 1. Cấu hình mạng
HOST=0.0.0.0
PORT=8003
AGENT_ID=ba-01
AGENT_ROLE=BA

# 2. Khóa bảo mật Bearer Token (nếu để trống, bỏ qua kiểm tra token)
AGENT_API_KEY=your_secure_random_token_here
MAX_UPLOAD_MB=50

# 3. Cấu hình Google Gemini API
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIzaSy...your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
LLM_TEMPERATURE=0.2
LLM_TIMEOUT_SECONDS=60

# 4. Thư mục lưu trữ
ARTIFACT_DIR=./artifacts
WORKSPACE_DIR=./workspace
```

> [!TIP]
> Agent hỗ trợ cả 2 tên biến API Key: `GEMINI_API_KEY` hoặc `LLM_API_KEY`. Nếu không có API Key, Agent sẽ tự động kích hoạt bộ sinh phân tích **Heuristic Engine chuẩn mực**, cho phép test offline 100% không gián đoạn.

---

## 🚀 6. Khởi động và vận hành

Khởi chạy FastAPI server với Uvicorn:

```powershell
python -m uvicorn api:app --host 0.0.0.0 --port 8003 --reload
```

Tài liệu Swagger UI tương tác trực tiếp có sẵn tại: `http://localhost:8003/docs`

---

## 📡 7. Tài liệu API (Endpoints)

### 7.1 `GET /health` (Public Heartbeat)
Kiểm tra trạng thái sẵn sàng của Agent (không cần Token).

**Response:**
```json
{
  "status": "healthy",
  "agent_id": "ba-01",
  "role": "BA",
  "version": "1.1.0",
  "timestamp": "2026-11-04T15:00:00Z",
  "uptime_seconds": 120
}
```

### 7.2 `GET /agent` (Metadata & Capabilities)
Lấy danh sách năng lực và danh mục tài liệu đặc tả của Agent.

**Headers:** `Authorization: Bearer <AGENT_API_KEY>` (nếu có cấu hình)

**Response:**
```json
{
  "agent_id": "ba-01",
  "role": "BA",
  "name": "Senior Business Analyst AI Agent",
  "version": "1.1.0",
  "status": "idle",
  "llm_provider": "gemini",
  "llm_model": "gemini-2.5-flash",
  "capabilities": [
    "business_requirement_analysis",
    "functional_requirements_moscow",
    "non_functional_requirements_iso25010",
    "invest_user_story_generation",
    "gherkin_acceptance_criteria",
    "formal_use_case_specification",
    "business_process_modeling",
    "conflict_and_gap_detection",
    "explicit_assumption_formulation"
  ],
  "artifacts_produced": [
    "REQUIREMENTS.md",
    "SRS.md",
    "USER_STORIES.md",
    "USE_CASES.md",
    "ACCEPTANCE_CRITERIA.md",
    "BUSINESS_PROCESS.md"
  ]
}
```

### 7.3 `POST /tasks` (Execute Analysis Pipeline)
Gửi yêu cầu phân tích nghiệp vụ. Agent sẽ kích hoạt pipeline, ghi ra 6 tài liệu và trả về kết quả.

**Request Body:**
```json
{
  "task_id": "task-project-001",
  "project_name": "E-Commerce Logistics Hub",
  "description": "Xây dựng hệ thống điều phối giao vận thông minh cho sàn TMĐT: Phân bổ đơn hàng tự động cho tài xế theo tọa độ GPS, theo dõi lộ trình thời gian thực, quản lý khiếu nại hoàn hàng và thanh toán COD. Độ trễ yêu cầu dưới 500ms, hỗ trợ 5.000 tài xế hoạt động đồng thời."
}
```

**Response (200 OK):**
```json
{
  "task_id": "task-project-001",
  "status": "completed",
  "agent_id": "ba-01",
  "project_name": "E-Commerce Logistics Hub",
  "summary": "Successfully completed comprehensive BA analysis for 'E-Commerce Logistics Hub'...",
  "metrics": {
    "functional_requirements_count": 4,
    "non_functional_requirements_count": 5,
    "user_stories_count": 4,
    "use_cases_count": 4,
    "assumptions_count": 3,
    "conflicts_count": 0,
    "clarification_questions_count": 3
  },
  "artifacts": [
    {
      "name": "REQUIREMENTS.md",
      "path": ".../artifacts/REQUIREMENTS.md",
      "size_bytes": 4512,
      "checksum": "a8f3b2c1...",
      "lines": 115
    },
    ...
  ],
  "handover_notes": {
    "to_system_architect": {"agent": "sa-01", "recommended_focus": "System boundaries, external interfaces..."},
    "to_database_administrator": {"agent": "dba-01", "recommended_focus": "Domain entities identified in Functional Requirements..."}
  }
}
```

### 7.4 `GET /artifacts` & `GET /artifacts/{filename}`
Xem danh sách hoặc tải nội dung từng tài liệu markdown trực tiếp qua HTTP.

---

## 🧪 8. Kiểm thử tự động (Testing)

Agent đi kèm bộ test toàn diện 19 ca kiểm thử:
- `test_tools.py`: Kiểm thử phân tích yêu cầu, sinh User Story và sinh Use Case.
- `test_agent.py`: Kiểm thử vòng đời BAAgent, sinh đủ 6 file và khóa concurrency lock.
- `test_api.py`: Kiểm thử các endpoint FastAPI, xác thực Bearer token, mã phản hồi 401, 404, 409.
- `test_document_quality.py`: Kiểm tra định dạng IEEE 830, Gherkin, INVEST, Mermaid diagram, bảo đảm **0% mã lập trình** và **0% mã SQL DDL**.

Chạy toàn bộ test suite:

```powershell
python -m pytest agents/ba/tests -v
```

---

## 🤝 9. Quy trình bàn giao đa tác tử (Multi-Agent Hand-off Protocol)

Sau khi BA Agent hoàn tất tác vụ, 6 tài liệu trong `artifacts/` sẽ sẵn sàng để PM Conductor trung chuyển:
1. **Bàn giao cho System Architect (`sa-01`)**: `SRS.md` và `BUSINESS_PROCESS.md` để thiết kế kiến trúc hệ thống và luồng tương tác giữa các service.
2. **Bàn giao cho Database Administrator (`dba-01`)**: `REQUIREMENTS.md` (mục Business Rules và FR) để DBA tiến hành chuẩn hóa mô hình dữ liệu quan hệ và viết `schema.sql`.
3. **Bàn giao cho Developer (`dev-01`)**: `USER_STORIES.md` và `REQUIREMENTS.md` để lập trình tính năng.
4. **Bàn giao cho QA Tester (`tester-01`)**: `ACCEPTANCE_CRITERIA.md` và `USE_CASES.md` để tự động hóa kịch bản test suite.
