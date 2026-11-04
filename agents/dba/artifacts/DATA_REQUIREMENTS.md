# Data Requirements Specification: STUDENT_MGMT_DB

> [!NOTE]
> **Document Version**: 1.0.0 | **Author**: Senior Database Architect (`dba-01`)
> **Source Requirement**: Business Analyst Specification (MediCare Health Portal)

## 1. Executive Summary & Data Architecture Scope
This document details the data requirements, entity definitions, attribute domains, and validation rules derived directly from the business specifications provided by Business Analyst AI Agent (`ba-01`).
The data model strictly implements **Third Normal Form (3NF)** with explicit, documented denormalizations for historical transaction stability.

---

## 2. Business Entity Catalog & Domain Definitions

| Entity Name | Storage Table | Classification | Estimated Growth (1 Year) | Retention Policy |
|---|---|---|---|---|
| Khoa / Vien dao tao quan ly cac nganh va lop hoc | `departments` | Core Master | 10,000 - 100,000 rows | Indefinite (Soft-delete only) |
| Lop sinh hoat hoc tap theo nien khoa | `classes` | Relational / Transactional | 10,000 - 100,000 rows | Indefinite (Soft-delete only) |
| Ho so thong tin sinh vien day du kem anh dai dien | `students` | Relational / Transactional | 10,000 - 100,000 rows | Indefinite (Soft-delete only) |
| Hoc phan chuong trinh dao tao | `courses` | Relational / Transactional | 10,000 - 100,000 rows | Indefinite (Soft-delete only) |
| Dang ky hoc phan va bang diem sinh vien | `enrollments` | Relational / Transactional | 10,000 - 100,000 rows | Indefinite (Soft-delete only) |
| Nhat ky kiem toan bat bien ghi lai cac thay doi ho so sinh vien | `student_audit_logs` | Immutable Audit Log | 1,000,000+ rows | 3 Years Legal Compliance |

---

## 3. Data Dictionary & Attribute Specifications

### Entity: `departments` (Khoa / Vien dao tao quan ly cac nganh va lop hoc)

| Column Name | Physical Data Type | Nullable | Primary / Unique | Check Constraint | Business Definition & Comments |
|---|---|---|---|---|---|
| `id` | `UUID` | NO | **PK** | - | Unique surrogate primary key (UUIDv4/v7) |
| `created_at` | `TIMESTAMPTZ` | NO | **-** | - | Timestamp when record was created |
| `updated_at` | `TIMESTAMPTZ` | NO | **-** | - | Timestamp when record was last updated |
| `deleted_at` | `TIMESTAMPTZ` | YES | **-** | - | Soft-delete timestamp; NULL indicates active record |
| `version` | `INTEGER` | NO | **-** | - | Optimistic locking version counter |
| `department_code` | `VARCHAR(30)` | NO | **UK** | - | Ma khoa duy nhat (VD: CNTT, DTVT) |
| `name` | `VARCHAR(150)` | NO | **-** | - | Ten day du cua khoa |
| `description` | `TEXT` | YES | **-** | - | Mo ta chuc nang nhiem vu khoa |
| `is_active` | `BOOLEAN` | NO | **-** | - | Trang thai hoat dong |

### Entity: `classes` (Lop sinh hoat hoc tap theo nien khoa)

| Column Name | Physical Data Type | Nullable | Primary / Unique | Check Constraint | Business Definition & Comments |
|---|---|---|---|---|---|
| `id` | `UUID` | NO | **PK** | - | Unique surrogate primary key (UUIDv4/v7) |
| `created_at` | `TIMESTAMPTZ` | NO | **-** | - | Timestamp when record was created |
| `updated_at` | `TIMESTAMPTZ` | NO | **-** | - | Timestamp when record was last updated |
| `deleted_at` | `TIMESTAMPTZ` | YES | **-** | - | Soft-delete timestamp; NULL indicates active record |
| `version` | `INTEGER` | NO | **-** | - | Optimistic locking version counter |
| `class_code` | `VARCHAR(30)` | NO | **UK** | - | Ma lop duy nhat (VD: D20CNTT1) |
| `name` | `VARCHAR(150)` | NO | **-** | - | Ten lop sinh hoat |
| `department_id` | `UUID` | NO | **-** | - | Tham chieu toi khoa quan ly |
| `academic_year` | `VARCHAR(30)` | NO | **-** | - | Nien khoa (VD: 2020-2025) |
| `is_active` | `BOOLEAN` | NO | **-** | - | Trang thai lop |

### Entity: `students` (Ho so thong tin sinh vien day du kem anh dai dien)

| Column Name | Physical Data Type | Nullable | Primary / Unique | Check Constraint | Business Definition & Comments |
|---|---|---|---|---|---|
| `id` | `UUID` | NO | **PK** | - | Unique surrogate primary key (UUIDv4/v7) |
| `created_at` | `TIMESTAMPTZ` | NO | **-** | - | Timestamp when record was created |
| `updated_at` | `TIMESTAMPTZ` | NO | **-** | - | Timestamp when record was last updated |
| `deleted_at` | `TIMESTAMPTZ` | YES | **-** | - | Soft-delete timestamp; NULL indicates active record |
| `version` | `INTEGER` | NO | **-** | - | Optimistic locking version counter |
| `student_code` | `VARCHAR(30)` | NO | **UK** | - | Ma so sinh vien duy nhat (VD: B20DCCN001) |
| `full_name` | `VARCHAR(150)` | NO | **-** | - | Ho va ten day du cua sinh vien |
| `gender` | `VARCHAR(10)` | NO | **-** | `gender IN ('MALE', 'FEMALE', 'OTHER')` | Gioi tinh sinh vien |
| `dob` | `DATE` | YES | **-** | - | Ngay thang nam sinh |
| `email` | `VARCHAR(255)` | NO | **UK** | - | Email lien he chinh thuc |
| `phone_number` | `VARCHAR(30)` | YES | **-** | - | So dien thoai di dong |
| `address` | `TEXT` | YES | **-** | - | Dia chi thuong tru hoac cu tru |
| `avatar_url` | `VARCHAR(500)` | YES | **-** | - | Duong dan luu anh dai dien upload |
| `class_id` | `UUID` | NO | **-** | - | Tham chieu toi lop sinh hoat |
| `status` | `VARCHAR(30)` | NO | **-** | `status IN ('ACTIVE', 'SUSPENDED', 'GRADUATED', 'DROPOUT')` | Trang thai hoc tap |

### Entity: `courses` (Hoc phan chuong trinh dao tao)

| Column Name | Physical Data Type | Nullable | Primary / Unique | Check Constraint | Business Definition & Comments |
|---|---|---|---|---|---|
| `id` | `UUID` | NO | **PK** | - | Unique surrogate primary key (UUIDv4/v7) |
| `created_at` | `TIMESTAMPTZ` | NO | **-** | - | Timestamp when record was created |
| `updated_at` | `TIMESTAMPTZ` | NO | **-** | - | Timestamp when record was last updated |
| `deleted_at` | `TIMESTAMPTZ` | YES | **-** | - | Soft-delete timestamp; NULL indicates active record |
| `version` | `INTEGER` | NO | **-** | - | Optimistic locking version counter |
| `course_code` | `VARCHAR(30)` | NO | **UK** | - | Ma mon hoc (VD: INT1306) |
| `name` | `VARCHAR(200)` | NO | **-** | - | Ten mon hoc |
| `credits` | `INTEGER` | NO | **-** | `credits > 0` | So tin chi |
| `department_id` | `UUID` | NO | **-** | - | Khoa phu trach mon hoc |

### Entity: `enrollments` (Dang ky hoc phan va bang diem sinh vien)

| Column Name | Physical Data Type | Nullable | Primary / Unique | Check Constraint | Business Definition & Comments |
|---|---|---|---|---|---|
| `id` | `UUID` | NO | **PK** | - | Unique surrogate primary key (UUIDv4/v7) |
| `created_at` | `TIMESTAMPTZ` | NO | **-** | - | Timestamp when record was created |
| `updated_at` | `TIMESTAMPTZ` | NO | **-** | - | Timestamp when record was last updated |
| `deleted_at` | `TIMESTAMPTZ` | YES | **-** | - | Soft-delete timestamp; NULL indicates active record |
| `version` | `INTEGER` | NO | **-** | - | Optimistic locking version counter |
| `student_id` | `UUID` | NO | **-** | - | Sinh vien tham gia hoc |
| `course_id` | `UUID` | NO | **-** | - | Mon hoc dang ky |
| `semester` | `VARCHAR(20)` | NO | **-** | - | Hoc ky dang ky (VD: 2026-1) |
| `attendance_score` | `NUMERIC(4, 2)` | YES | **-** | `attendance_score >= 0 AND attendance_score <= 10` | Diem chuyen can |
| `midterm_score` | `NUMERIC(4, 2)` | YES | **-** | `midterm_score >= 0 AND midterm_score <= 10` | Diem giua ky |
| `final_score` | `NUMERIC(4, 2)` | YES | **-** | `final_score >= 0 AND final_score <= 10` | Diem thi ket thuc hoc phan |
| `status` | `VARCHAR(30)` | NO | **-** | `status IN ('IN_PROGRESS', 'PASSED', 'FAILED', 'WITHDRAWN')` | Trang thai hoan thanh |

### Entity: `student_audit_logs` (Nhat ky kiem toan bat bien ghi lai cac thay doi ho so sinh vien)

| Column Name | Physical Data Type | Nullable | Primary / Unique | Check Constraint | Business Definition & Comments |
|---|---|---|---|---|---|
| `id` | `UUID` | NO | **PK** | - | Surrogate primary key |
| `created_at` | `TIMESTAMPTZ` | NO | **-** | - | Thoi diem xay ra su kien |
| `student_id` | `UUID` | YES | **-** | - | Sinh vien bi tac dong |
| `action` | `VARCHAR(50)` | NO | **-** | - | Loai thao tac: CREATE, UPDATE, DELETE, UPLOAD_AVATAR |
| `changed_by` | `VARCHAR(100)` | NO | **-** | - | Tai khoan thuc hien |
| `old_values` | `JSONB` | YES | **-** | - | Gia tri truoc khi sua |
| `new_values` | `JSONB` | YES | **-** | - | Gia tri sau khi sua |
| `ip_address` | `VARCHAR(45)` | YES | **-** | - | IP client |

---

## 4. Referential Integrity & Deletion Rules
- **Master Entities**: Protected by `ON DELETE RESTRICT`. Master records with active dependencies cannot be deleted directly.
- **Child / Composition Entities**: Bound to parent entities with `ON DELETE CASCADE` or `RESTRICT` depending on business domain lifecycle.
- **Audit Log Entities**: Strictly append-only. References to deleted parent entities use `ON DELETE SET NULL` to preserve historical event integrity.