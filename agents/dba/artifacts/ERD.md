# Entity-Relationship Diagram (ERD): STUDENT_MGMT_DB

> [!NOTE]
> **Database Architecture**: student_mgmt_db | Dialect: POSTGRESQL 16+ | Designed by: DBA AI Agent (`dba-01`)

## 1. Visual ER Diagram

```mermaid
erDiagram
    DEPARTMENTS ||--|{ CLASSES : "department_id"
    CLASSES ||--|{ STUDENTS : "class_id"
    DEPARTMENTS ||--|{ COURSES : "department_id"
    STUDENTS ||--|{ ENROLLMENTS : "student_id"
    COURSES ||--|{ ENROLLMENTS : "course_id"
    STUDENTS ||--o{ STUDENT_AUDIT_LOGS : "student_id"

    DEPARTMENTS {
        uuid id PK "Unique surrogate primary key (UUIDv4/v7)"
        timestamptz created_at "Timestamp when record was created"
        timestamptz updated_at "Timestamp when record was last updated"
        timestamptz deleted_at "Soft-delete timestamp; NULL indicates active record"
        integer version "Optimistic locking version counter"
        varchar department_code UK "Ma khoa duy nhat (VD: CNTT, DTVT)"
        varchar name "Ten day du cua khoa"
        text description "Mo ta chuc nang nhiem vu khoa"
        boolean is_active "Trang thai hoat dong"
    }
    CLASSES {
        uuid id PK "Unique surrogate primary key (UUIDv4/v7)"
        timestamptz created_at "Timestamp when record was created"
        timestamptz updated_at "Timestamp when record was last updated"
        timestamptz deleted_at "Soft-delete timestamp; NULL indicates active record"
        integer version "Optimistic locking version counter"
        varchar class_code UK "Ma lop duy nhat (VD: D20CNTT1)"
        varchar name "Ten lop sinh hoat"
        uuid department_id FK "Tham chieu toi khoa quan ly"
        varchar academic_year "Nien khoa (VD: 2020-2025)"
        boolean is_active "Trang thai lop"
    }
    STUDENTS {
        uuid id PK "Unique surrogate primary key (UUIDv4/v7)"
        timestamptz created_at "Timestamp when record was created"
        timestamptz updated_at "Timestamp when record was last updated"
        timestamptz deleted_at "Soft-delete timestamp; NULL indicates active record"
        integer version "Optimistic locking version counter"
        varchar student_code UK "Ma so sinh vien duy nhat (VD: B20DCCN001)"
        varchar full_name "Ho va ten day du cua sinh vien"
        varchar gender "Gioi tinh sinh vien"
        date dob "Ngay thang nam sinh"
        varchar email UK "Email lien he chinh thuc"
        varchar phone_number "So dien thoai di dong"
        text address "Dia chi thuong tru hoac cu tru"
        varchar avatar_url "Duong dan luu anh dai dien upload"
        uuid class_id FK "Tham chieu toi lop sinh hoat"
        varchar status "Trang thai hoc tap"
    }
    COURSES {
        uuid id PK "Unique surrogate primary key (UUIDv4/v7)"
        timestamptz created_at "Timestamp when record was created"
        timestamptz updated_at "Timestamp when record was last updated"
        timestamptz deleted_at "Soft-delete timestamp; NULL indicates active record"
        integer version "Optimistic locking version counter"
        varchar course_code UK "Ma mon hoc (VD: INT1306)"
        varchar name "Ten mon hoc"
        integer credits "So tin chi"
        uuid department_id FK "Khoa phu trach mon hoc"
    }
    ENROLLMENTS {
        uuid id PK "Unique surrogate primary key (UUIDv4/v7)"
        timestamptz created_at "Timestamp when record was created"
        timestamptz updated_at "Timestamp when record was last updated"
        timestamptz deleted_at "Soft-delete timestamp; NULL indicates active record"
        integer version "Optimistic locking version counter"
        uuid student_id FK "Sinh vien tham gia hoc"
        uuid course_id FK "Mon hoc dang ky"
        varchar semester "Hoc ky dang ky (VD: 2026-1)"
        numeric attendance_score "Diem chuyen can"
        numeric midterm_score "Diem giua ky"
        numeric final_score "Diem thi ket thuc hoc phan"
        varchar status "Trang thai hoan thanh"
    }
    STUDENT_AUDIT_LOGS {
        uuid id PK "Surrogate primary key"
        timestamptz created_at "Thoi diem xay ra su kien"
        uuid student_id FK "Sinh vien bi tac dong"
        varchar action "Loai thao tac: CREATE, UPDATE, DELETE, UPLOAD_AVATAR"
        varchar changed_by "Tai khoan thuc hien"
        jsonb old_values "Gia tri truoc khi sua"
        jsonb new_values "Gia tri sau khi sua"
        varchar ip_address "IP client"
    }
```

---

## 2. Entity Catalog & Domain Breakdown

| Entity / Table Name | Primary Key | Description | Traceability / BA Requirement |
|---|---|---|---|
| `departments` | `id` | Khoa / Vien dao tao quan ly cac nganh va lop hoc | FR-01 |
| `classes` | `id` | Lop sinh hoat hoc tap theo nien khoa | FR-01 |
| `students` | `id` | Ho so thong tin sinh vien day du kem anh dai dien | FR-02 |
| `courses` | `id` | Hoc phan chuong trinh dao tao | FR-03 |
| `enrollments` | `id` | Dang ky hoc phan va bang diem sinh vien | FR-03 |
| `student_audit_logs` | `id` | Nhat ky kiem toan bat bien ghi lai cac thay doi ho so sinh vien | FR-04 |

---

## 3. Relationship Matrix & Integrity Rules

| Parent Entity | Child Entity | Foreign Key Column | Cardinality | ON DELETE Action | Business Semantics |
|---|---|---|---|---|---|
| `departments` | `classes` | `department_id` -> `id` | `1 : 1..N` | `RESTRICT` | Child `classes` belongs to parent `departments` |
| `classes` | `students` | `class_id` -> `id` | `1 : 1..N` | `RESTRICT` | Child `students` belongs to parent `classes` |
| `departments` | `courses` | `department_id` -> `id` | `1 : 1..N` | `RESTRICT` | Child `courses` belongs to parent `departments` |
| `students` | `enrollments` | `student_id` -> `id` | `1 : 1..N` | `CASCADE` | Child `enrollments` belongs to parent `students` |
| `courses` | `enrollments` | `course_id` -> `id` | `1 : 1..N` | `RESTRICT` | Child `enrollments` belongs to parent `courses` |
| `students` | `student_audit_logs` | `student_id` -> `id` | `1 : 0..N` | `SET NULL` | Child `student_audit_logs` belongs to parent `students` |

---

## 4. Key Design Decisions & Normalization Rationale
- **Surrogate Keys**: Standardized on UUIDv7 / UUIDv4 across all tables for distributed uniqueness and security.
- **Referential Actions**: Mission-critical master records employ `RESTRICT` to prevent accidental orphaned deletions; child composition details (e.g. line items) use `CASCADE`.
- **Audit Standard**: All tables include `created_at`, `updated_at`, `deleted_at` (soft delete), and `version`.