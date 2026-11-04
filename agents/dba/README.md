# DBA AI Agent (Database Administrator - `dba-01`)
### Senior Database Architect & Engineering Agent

Agent Database Administrator độc lập bằng Python thuộc hệ sinh thái Multi-Agent Software Engineering. DBA Agent chịu trách nhiệm tiếp nhận tài liệu yêu cầu nghiệp vụ (SRS) từ BA Agent (`ba-01`), phân tích cấu trúc dữ liệu, thiết kế mô hình dữ liệu quan hệ hoàn chỉnh, chuẩn hóa dữ liệu, tối ưu truy vấn, đề xuất chỉ mục (indexes), và biên dịch DDL SQL đạt chuẩn sản xuất.

---

## 📁 1. Cấu trúc thư mục

```text
agents/dba/
├── api.py                      # FastAPI REST API (chuẩn Agent API v1 & multi-machine)
├── agent.py                    # DBAAgent core engine điều phối quy trình phân tích và thiết kế
├── prompts/
│   └── dba_system_prompt.md    # System prompt chuyên sâu cho Senior Database Architect
├── tools/
│   ├── schema_generator.py     # Mô hình hóa thực thể, quan hệ, topological sort, sinh DDL
│   ├── sql_validator.py        # Kiểm tra cú pháp, quy tắc an toàn, kiểm thử in-memory SQLite
│   ├── erd_generator.py        # Sinh sơ đồ Mermaid erDiagram chuẩn và từ điển thực thể
│   ├── query_optimizer.py      # Phát hiện anti-pattern, tư vấn tối ưu truy vấn & chiến lược Index
│   └── llm_client.py           # Tích hợp Google Gemini API kèm cơ chế fallback ngoại tuyến
├── workspace/                  # Thư mục chứa tài liệu đầu vào (SRS từ BA) và kết quả làm việc
├── artifacts/                  # Thư mục lưu trữ 6 artifact đầu ra chính thức
├── tests/                      # Bộ kiểm thử Unit Test & Integration Test toàn diện
│   ├── test_schema_generator.py
│   ├── test_sql_validator.py
│   ├── test_erd_generator.py
│   ├── test_query_optimizer.py
│   ├── test_agent.py
│   └── test_api.py
├── requirements.txt            # Thư viện phụ thuộc
├── .env.example                # File mẫu cấu hình biến môi trường
└── README.md                   # Tài liệu hướng dẫn sử dụng và đặc tả kỹ thuật
```

---

## ⚡ 2. Năng lực cốt lõi

- **Tiếp nhận & Đọc hiểu SRS từ BA**: Phân tích tài liệu đặc tả yêu cầu phần mềm, trích xuất thực thể, thuộc tính, quy tắc nghiệp vụ và ràng buộc miền giá trị.
- **Xác định Primary Key & Foreign Key**:
  - Khuyến nghị khóa đại diện chuẩn `UUIDv7` / `UUIDv4` phân tán bảo mật.
  - Thiết lập chính xác hành động toàn vẹn tham chiếu (`ON DELETE RESTRICT`, `CASCADE`, `SET NULL`).
- **Thiết kế ERD**: Sinh sơ đồ quan hệ thực thể chuẩn Mermaid `erDiagram` trực quan, kèm ma trận quan hệ và bảng từ điển thực thể.
- **Chuẩn hóa dữ liệu (1NF -> 3NF & BCNF)**: Loại bỏ triệt để dị thường cập nhật và phụ thuộc bắc cầu; giải thích và kiểm soát rõ ràng mọi quyết định phi chuẩn hóa có chủ đích (intentional denormalization) phục vụ hiệu năng hoặc bảo toàn giá lịch sử.
- **Biên dịch SQL DDL chuẩn sản xuất**:
  - Hỗ trợ chính: **PostgreSQL 16+** (tương thích ANSI SQL).
  - Tự động sắp xếp thứ tự tạo bảng theo giải thuật **Topological Sort** (bảo đảm bảng cha được tạo trước bảng con, không gặp lỗi foreign key).
  - Tự động tích hợp bộ cột kiểm toán chuẩn doanh nghiệp: `id`, `created_at`, `updated_at`, `deleted_at` (soft-delete), `version` (optimistic locking), và trigger cập nhật `updated_at`.
- **An toàn dữ liệu tuyệt đối (Zero Destruction Rule)**:
  - Bộ quy tắc chặn các câu lệnh nguy hiểm: cấm `DROP DATABASE`, cấm `TRUNCATE TABLE`, cấm `DELETE` không có `WHERE`, bắt buộc `IF EXISTS` khi DROP.
- **Kiểm thử Schema In-Memory trên SQLite**: Biên dịch và chạy thử nghiệm trực tiếp trên bộ nhớ RAM (`:memory:`) với cờ `PRAGMA foreign_keys = ON;` để kiểm tra tính toàn vẹn 100% trước khi bàn giao.
- **Chiến lược Index & Tối ưu truy vấn**:
  - Tự động thiết lập Index cho tất cả khóa ngoại (FK) tránh lock bảng.
  - Khuyến nghị Composite Index (tuân thủ Leftmost Prefix Rule), Partial Index cho bảng có soft-delete, và GIN Index cho trường JSONB.
  - Phân tích và phát hiện anti-pattern: `SELECT *`, Leading Wildcard `LIKE '%...'`, hàm non-SARGable trong `WHERE`, và phân trang sâu `OFFSET`.

---

## 📄 3. Danh mục 6 Artifact đầu ra bắt buộc

Mỗi khi DBA Agent hoàn thành tác vụ thiết kế cơ sở dữ liệu, agent sẽ sinh ra đầy đủ 6 tài liệu tại thư mục `artifacts/` và `workspace/`:

| Tên Artifact | Định dạng | Nội dung chi tiết |
|---|---|---|
| **`DATA_REQUIREMENTS.md`** | Markdown | Danh mục thực thể, miền giá trị thuộc tính, ước lượng dung lượng dữ liệu, chính sách lưu trữ (retention policy), quy tắc nullability. |
| **`ERD.md`** | Markdown | Sơ đồ Mermaid `erDiagram`, từ điển thực thể chi tiết, ma trận quan hệ cha-con kèm giải thích cardinality. |
| **`DATABASE_DESIGN.md`** | Markdown | Kiến trúc CSDL tổng thể, lý do chọn hệ quản trị, phân tích chuẩn hóa 3NF, cơ chế khóa dòng / mức cô lập giao dịch (ACID), giải pháp Soft Delete và kiểm toán. |
| **`schema.sql`** | SQL DDL | Kịch bản DDL hoàn chỉnh, sắp xếp theo Topological Sort, đầy đủ constraints, triggers, và indexes đã được kiểm thử in-memory. |
| **`INDEX_STRATEGY.md`** | Markdown | Danh mục toàn bộ chỉ mục, phân tích đánh đổi chi phí ghi/đọc, khuyến nghị phân trang keyset, quy trình bảo trì (`REINDEX CONCURRENTLY`, `ANALYZE`). |
| **`DATABASE_REVIEW.md`** | Markdown | Ma trận truy xuất nguồn gốc hai chiều (Traceability Matrix: BA Requirement -> DB Table.Column), báo cáo nghiệm thu an toàn SQL, và khuyến nghị bàn giao cho Dev & QA. |

---

## 🔌 4. Đặc tả REST API (FastAPI)

Agent triển khai REST API chuẩn **Agent API v1** chạy trên cổng mặc định `8008`:

### Các Endpoints chính:
- **`GET /health`** (Public - không cần token):
  Kiểm tra trạng thái hoạt động của agent, trạng thái LLM, phiên bản và trạng thái IDLE/BUSY.
- **`GET /agent`** (Protected):
  Trả về thông tin metadata, vai trò (`DBA`), danh sách năng lực và các artifact đầu ra bắt buộc.
- **`GET /state`** (Protected):
  Kiểm tra trạng thái agent đang bận (`BUSY`) xử lý task nào hay đang rảnh (`IDLE`).
- **`POST /tasks`** (Protected):
  Giao việc thiết kế CSDL cho DBA Agent. Body nhận JSON chứa `requirements` (hoặc `brief`, `content`, hoặc `file_path`). Agent sẽ thực thi toàn bộ pipeline và trả về link tải 6 artifact kèm báo cáo kiểm tra.
- **`GET /artifacts`** (Protected):
  Liệt kê danh sách tất cả artifact đã sinh kèm dung lượng và mã băm SHA-256.
- **`GET /artifacts/{id}/content`** (Protected):
  Tải nội dung chi tiết của một artifact (ví dụ: `schema.sql`, `ERD.md`).
- **`POST /artifacts/inbox`** (Protected):
  Nhận tài liệu được trung chuyển qua mạng từ BA Agent (`ba-01`) hoặc PM Conductor.

---

## 🤖 5. Cấu hình Model AI (Google Gemini)

Agent hỗ trợ **Google Gemini API** qua thư viện `google-generativeai`. Cấu hình thông qua file `.env`:

```properties
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
LLM_TEMPERATURE=0.1
LLM_TIMEOUT_SECONDS=60
```

> [!NOTE]
> Khi không có `GEMINI_API_KEY` (hoặc mạng ngoại tuyến), DBA Agent tự động kích hoạt **Deterministic Architectural Fallback Engine** dựa trên các mẫu kiến trúc doanh nghiệp chuẩn, bảo đảm 100% các bài test và quy trình sinh DDL / ERD / Review luôn thành công tuyệt đối và không phụ thuộc mạng.

---

## 🛠️ 6. Cài đặt và Khởi chạy

### Bước 1: Kích hoạt môi trường và cài đặt thư viện
```bash
cd agents/dba
pip install -r requirements.txt
```

### Bước 2: Thiết lập biến môi trường
Tạo file `.env` từ file mẫu:
```bash
cp .env.example .env
```
Điền `GEMINI_API_KEY` nếu bạn muốn sử dụng tính năng sinh tự động với Gemini.

### Bước 3: Khởi chạy dịch vụ API
```bash
python -m uvicorn agents.dba.api:app --host 0.0.0.0 --port 8008 --reload
```
Hoặc chạy trực tiếp từ thư mục `agents/dba`:
```bash
cd agents/dba
python -m uvicorn api:app --host 0.0.0.0 --port 8008 --reload
```

Truy cập Swagger UI tài liệu API tại: `http://localhost:8008/docs`

---

## 🧪 7. Chạy kiểm thử tự động (Unit & Integration Tests)

DBA Agent đi kèm bộ kiểm thử đầy đủ kiểm tra cú pháp SQL, toàn vẹn khóa ngoại, sinh ERD, tối ưu truy vấn, pipeline sinh 6 artifact và toàn bộ API endpoint:

```bash
# Chạy toàn bộ test suite từ thư mục gốc
pytest agents/dba/tests/ -v

# Hoặc chạy kiểm tra chi tiết kèm đo lường
pytest agents/dba/tests/test_agent.py -v
pytest agents/dba/tests/test_api.py -v
```
