# Database Indexing Strategy: STUDENT_MGMT_DB

> [!IMPORTANT]
> **Senior DBA Index Governance Policy**: Every index represents a trade-off between read acceleration and write overhead (INSERT/UPDATE/DELETE page maintenance and WAL volume). All indexes documented below are strictly justified by access paths.

## 1. Index Architecture Principles
1. **Mandatory Foreign Key Coverage**: Every foreign key is explicitly indexed to avoid full table scans during child table JOINs and table-level share locks during parent key mutations.
2. **Leftmost Prefix Rule Compliance**: Multi-column composite indexes are arranged with high-cardinality equality filters first, followed by range predicates or sorting columns (`WHERE a = ? AND b = ? ORDER BY c`).
3. **Partial / Filtered Index Optimization**: Tables with soft-deletes (`deleted_at`) employ partial indexes (`WHERE deleted_at IS NULL`) to prune index tree depth by 30-70% and reduce write-amplification.
4. **Index Method Specialization**: Standard B-Tree for equality and range scans; GIN for document/JSONB containment (`@>`) or full-text vectors.

---

## 2. Comprehensive Index Inventory

| Target Table | Index Name | Columns Indexed | Method | Partial Condition (WHERE) | Architectural Rationale |
|---|---|---|---|---|---|
| `classes` | `idx_classes_department_id` | `department_id` | `BTREE` | *Unconditional* | Accelerates JOINs on foreign key department_id -> departments.id |
| `students` | `idx_students_student_code` | `student_code` | `BTREE` | *Unconditional* | Tra cuu nhanh theo ma sinh vien |
| `students` | `idx_students_full_name` | `full_name` | `BTREE` | *Unconditional* | Tim kiem sinh vien theo ho ten |
| `students` | `idx_students_class_id` | `class_id` | `BTREE` | *Unconditional* | Loc danh sach sinh vien theo lop |
| `students` | `idx_students_email` | `email` | `BTREE` | *Unconditional* | Tra cuu tai khoan qua email |
| `students` | `idx_students_active_status` | `status` | `BTREE` | `"deleted_at" IS NULL` | Partial index for active non-deleted records filtering by status |
| `courses` | `idx_courses_department_id` | `department_id` | `BTREE` | *Unconditional* | Accelerates JOINs on foreign key department_id -> departments.id |
| `enrollments` | `idx_enrollments_student_id` | `student_id` | `BTREE` | *Unconditional* | Accelerates JOINs on foreign key student_id -> students.id |
| `enrollments` | `idx_enrollments_course_id` | `course_id` | `BTREE` | *Unconditional* | Accelerates JOINs on foreign key course_id -> courses.id |
| `enrollments` | `idx_enrollments_active_status` | `status` | `BTREE` | `"deleted_at" IS NULL` | Partial index for active non-deleted records filtering by status |
| `student_audit_logs` | `idx_student_audit_logs_student_id` | `student_id` | `BTREE` | *Unconditional* | Accelerates JOINs on foreign key student_id -> students.id |
| `student_audit_logs` | `idx_student_audit_logs_old_values_gin` | `old_values` | `GIN` | *Unconditional* | GIN index for arbitrary key-value search within old_values JSON payload |
| `student_audit_logs` | `idx_student_audit_logs_new_values_gin` | `new_values` | `GIN` | *Unconditional* | GIN index for arbitrary key-value search within new_values JSON payload |

---

## 3. Query Workload Optimization & Anti-Pattern Mitigation

### A. Keyset Pagination vs. Offset Pagination
Traditional `OFFSET` requires scanning and discarding prior records. In production, use cursor-based keyset pagination:
```sql
-- High-performance cursor pagination:
SELECT id, created_at, status
FROM orders
WHERE created_at < :last_seen_created_at
ORDER BY created_at DESC
LIMIT 20;
```

### B. Avoiding Non-SARGable Predicates
- **Do NOT do**: `WHERE LOWER(email) = LOWER(:input)` (causes full table scan).
- **Do instead**: Standardize emails to lowercase upon write, or use an expression index: `CREATE UNIQUE INDEX idx_users_email_lower ON users (LOWER(email));`

---

## 4. Maintenance & Monitoring Guidelines (Day-2 Operations)
1. **Detect Unused Indexes**: Run monthly audit using PostgreSQL stats:
   ```sql
   SELECT schemaname, relname, indexrelname, idx_scan
   FROM pg_stat_user_indexes
   WHERE idx_scan = 0 AND indexrelname NOT LIKE '%_pkey'
   ORDER BY relname;
   ```
2. **Zero-Downtime Index Rebuilding**: In production, always use `CONCURRENTLY` to avoid write table locks:
   ```sql
   REINDEX TABLE CONCURRENTLY orders;
   ```
3. **Statistics Freshness**: Ensure PostgreSQL autovacuum is tuned, or trigger `ANALYZE` after large batch ingestions.