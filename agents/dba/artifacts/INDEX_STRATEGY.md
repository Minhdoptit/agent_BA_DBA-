# Database Indexing Strategy: STUDENT_MANAGEMENT_SYSTEM

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
| `categories` | `idx_categories_parent_id` | `parent_id` | `BTREE` | *Unconditional* | Accelerates JOINs on foreign key parent_id -> categories.id |
| `products` | `idx_products_category_id` | `category_id` | `BTREE` | *Unconditional* | Accelerates JOINs on foreign key category_id -> categories.id |
| `products` | `idx_products_metadata_gin` | `metadata` | `GIN` | *Unconditional* | GIN index for arbitrary key-value search within metadata JSON payload |
| `orders` | `idx_orders_user_id` | `user_id` | `BTREE` | *Unconditional* | Accelerates JOINs on foreign key user_id -> users.id |
| `orders` | `idx_orders_active_status` | `status` | `BTREE` | `"deleted_at" IS NULL` | Partial index for active non-deleted records filtering by status |
| `order_items` | `idx_order_items_order_id` | `order_id` | `BTREE` | *Unconditional* | Accelerates JOINs on foreign key order_id -> orders.id |
| `order_items` | `idx_order_items_product_id` | `product_id` | `BTREE` | *Unconditional* | Accelerates JOINs on foreign key product_id -> products.id |
| `payments` | `idx_payments_order_id` | `order_id` | `BTREE` | *Unconditional* | Accelerates JOINs on foreign key order_id -> orders.id |
| `payments` | `idx_payments_active_status` | `status` | `BTREE` | `"deleted_at" IS NULL` | Partial index for active non-deleted records filtering by status |
| `payments` | `idx_payments_gateway_payload_gin` | `gateway_payload` | `GIN` | *Unconditional* | GIN index for arbitrary key-value search within gateway_payload JSON payload |
| `audit_logs` | `idx_audit_logs_user_id` | `user_id` | `BTREE` | *Unconditional* | Accelerates JOINs on foreign key user_id -> users.id |
| `audit_logs` | `idx_audit_logs_changes_gin` | `changes` | `GIN` | *Unconditional* | GIN index for arbitrary key-value search within changes JSON payload |

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