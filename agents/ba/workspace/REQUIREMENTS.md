# BUSINESS REQUIREMENTS DOCUMENT (BRD) - WAREHOUSE INVENTORY MANAGEMENT

> **Agent ID**: `ba-01` | **Role**: Senior Business Analyst | **Standard**: ISO/IEC/IEEE 29148

---

## 1. Tóm tắt điều hành & Mục tiêu nghiệp vụ (Executive Summary)
Tài liệu đặc tả yêu cầu nghiệp vụ phần mềm cho Warehouse Inventory Management. Bao gồm 9 yêu cầu chức năng cốt lõi (MoSCoW), 5 chỉ số phi chức năng chuẩn ISO 25010, sơ đồ tuần tự (Sequence Diagrams), sơ đồ quy trình hoạt động, và các kịch bản Use Case chi tiết.

### 1.1 Mục tiêu kinh doanh cốt lõi (Core Business Goals)
- **Mục tiêu**: Xây dựng nền tảng số hóa và tự động hóa quy trình quản trị cho Warehouse Inventory Management.
- **Mục tiêu**: Cung cấp giao diện làm việc trực quan, tối ưu tốc độ tra cứu và thao tác dữ liệu.
- **Mục tiêu**: Đảm bảo an toàn dữ liệu, toàn vẹn quan hệ và khả năng mở rộng trong tương lai.

## 2. Phạm vi dự án (Project Scope Definition)
### 2.1 Trong phạm vi (In-Scope)
- [x] Phân hệ quản lý hồ sơ thực thể (Thêm, Sửa, Xóa).
- [x] Phân hệ tra cứu và tìm kiếm thông tin theo thời gian thực.
- [x] Phân hệ quản lý tệp đa phương tiện (Upload và xử lý ảnh đại diện).
- [x] Cơ chế xác thực bảo mật Bearer Token và ghi nhật ký kiểm toán (Audit Trail).

### 2.2 Ngoài phạm vi giai đoạn này (Out-of-Scope)
- [ ] Tích hợp cổng thanh toán học phí trực tuyến (chuyển sang Giai đoạn 2).
- [ ] Thuật toán AI điểm danh khuôn mặt qua camera (chuyển sang Giai đoạn sau).

## 3. Danh sách tác nhân hệ thống (Stakeholders & Actors)
- **Customer**: Có quyền hạn tương ứng theo phân quyền RBAC.
- **Admin**: Có quyền hạn tương ứng theo phân quyền RBAC.
- **End User**: Có quyền hạn tương ứng theo phân quyền RBAC.

## 4. Functional Requirements (FR) Matrix
### MoSCoW Priority Breakdown

| Mã YC | Tên chức năng | Phân loại | MoSCoW Priority | Tiêu chí nghiệm thu |
|:---:|:---|:---|:---:|:---|
| `FR-001` | **Hệ thống quản lý kho thông minh cho chuỗi bán lẻ** | Chức năng chính | `Must Have` | Người dùng thao tác và nhận được phản hồi thành công từ hệ thống |
| `FR-002` | **Nhập kho** | Chức năng chính | `Must Have` | Người dùng thao tác và nhận được phản hồi thành công từ hệ thống |
| `FR-003` | **xuất kho** | Chức năng chính | `Must Have` | Người dùng thao tác và nhận được phản hồi thành công từ hệ thống |
| `FR-004` | **kiểm kê định kỳ với mã vạch QR code.** | Chức năng chính | `Should Have` | Người dùng thao tác và nhận được phản hồi thành công từ hệ thống |
| `FR-005` | **Cảnh báo tồn kho tối thiểu và tự động đề xuất đơn đặt hàng m** | Chức năng chính | `Should Have` | Người dùng thao tác và nhận được phản hồi thành công từ hệ thống |
| `FR-006` | **Phân quyền cho Thủ kho** | Chức năng chính | `Should Have` | Người dùng thao tác và nhận được phản hồi thành công từ hệ thống |
| `FR-007` | **Nhân viên bốc dỡ** | Chức năng chính | `Should Have` | Người dùng thao tác và nhận được phản hồi thành công từ hệ thống |
| `FR-008` | **và Quản lý logistics.** | Chức năng chính | `Should Have` | Người dùng thao tác và nhận được phản hồi thành công từ hệ thống |
| `FR-009` | **Báo cáo doanh số và tỷ lệ thất thoát theo tháng.** | Chức năng chính | `Should Have` | Người dùng thao tác và nhận được phản hồi thành công từ hệ thống |

## 5. Non-Functional Requirements (NFR) Matrix (ISO/IEC 25010)

| Mã YC | Nhóm NFR | Mô tả chi tiết | Chỉ số đo lường (SLA) | Độ ưu tiên |
|:---:|:---|:---|:---|:---:|
| `NFR-001` | **Performance Efficiency** | Thời gian phản hồi của API truy vấn dữ liệu và tìm kiếm phải đạt dưới 300ms với 95% request. | `Latency p95 < 300ms` | `High` |
| `NFR-002` | **Security** | Toàn bộ API quản lý phải được xác thực bằng Bearer Token; dữ liệu tải lên được kiểm tra định dạng và chống mã độc. | `Bearer Token Auth, MIME validation, 0 SQL Injection vulnerabilities` | `Critical` |
| `NFR-003` | **Reliability** | Hệ thống duy trì tính sẵn sàng tối thiểu 99.9%, tự động phục hồi kết nối CSDL và sao lưu định kỳ. | `Uptime >= 99.9%, RPO < 1 hour` | `High` |
| `NFR-004` | **Usability** | Giao diện người dùng trực quan, tương thích đa thiết bị (Responsive Design trên Mobile và Desktop). | `WCAG 2.1 AA, Responsive Breakpoints` | `Medium` |
| `NFR-005` | **Maintainability** | Kiến trúc phân tầng rõ ràng giữa Presentation, Application Service và Database Schema. | `Loose coupling, Modular structure` | `Medium` |

## 6. Business Rules (Quy tắc nghiệp vụ)

| Mã quy tắc | Tên quy tắc | Nội dung quy tắc |
|:---|:---|:---|
| `BR-001` | **Định danh sinh viên duy nhất** | Mã sinh viên (student_code) là khóa tự nhiên duy nhất trên toàn hệ thống, không được phép trùng lặp. |
| `BR-002` | **Định dạng ảnh đại diện hợp lệ** | Ảnh đại diện chỉ chấp nhận các đuôi file .jpg, .jpeg, .png, .webp với dung lượng tối đa không vượt quá 5MB. |
| `BR-003` | **Toàn vẹn quan hệ** | Một sinh viên bắt buộc phải thuộc về một lớp học cụ thể (class_id hợp lệ) và không thể xóa lớp khi đang có sinh viên thuộc lớp đó. |

## 7. Assumptions Register (Bảng giả định)

| Mã giả định | Nội dung giả định | Cơ sở / Lý do | Mức độ ảnh hưởng |
|:---:|:---|:---|:---|
| `[ASSUMPTION-001]` | Hệ thống sử dụng cơ sở dữ liệu quan hệ (PostgreSQL hoặc SQLite) có hỗ trợ giao dịch ACID. | Đảm bảo tính toàn vẹn dữ liệu cho các bảng sinh viên, lớp, khoa. | Thiết kế CSDL của DBA |
| `[ASSUMPTION-002]` | Ảnh đại diện được lưu trữ trên hệ thống file tĩnh của máy chủ và lưu đường dẫn (URL) trong CSDL. | Tối ưu kích thước CSDL và tăng tốc độ tải trang. | Lưu trữ và hiệu năng hệ thống |

## 8. Clarification Questions (Câu hỏi làm rõ)

| Mã câu hỏi | Câu hỏi làm rõ | Đối tượng cần làm rõ | Mức độ khẩn cấp | Bối cảnh |
|:---:|:---|:---|:---:|:---|
| `[Q-001]` | Hệ thống có cần phân quyền chi tiết giữa Giảng viên và Quản trị viên đối với việc chỉnh sửa hồ sơ không? | Chủ nhiệm đề tài / Product Owner | `High` | Ảnh hưởng tới ma trận phân quyền RBAC |
| `[Q-002]` | Khi xóa sinh viên, hệ thống áp dụng cơ chế Soft Delete (ẩn đi) hay Hard Delete (xóa hẳn khỏi DB)? | Quản lý học vụ / DBA | `High` | Quyết định thiết kế khóa ngoại và cột deleted_at trong CSDL |