# Database Architectural Design: STUDENT_MANAGEMENT_SYSTEM

> [!TIP]
> **Senior Database Architect Assessment**: Production-grade relational schema optimized for high concurrency, ACID transaction consistency, and long-term scalability.

## 1. Architectural Principles & Engine Selection
- **Primary RDBMS Engine**: PostgreSQL 16+ (ANSI SQL-2016 Compliant).
- **Rationale for PostgreSQL**:
  1. Native JSONB with GIN indexing for flexible semi-structured metadata.
  2. Robust ACID compliance and fine-grained MVCC concurrency control.
  3. Rich constraint ecosystem (CHECK constraints, regex matching, partial indexes).
  4. First-class support for UUIDv4/UUIDv7 primary keys.

## 2. Normalization Analysis (1NF to 3NF)
1. **First Normal Form (1NF)**:
   - All columns store atomic values. No repeating groups or comma-separated lists.
   - Every table possesses an immutable Primary Key (`id UUID`).
2. **Second Normal Form (2NF)**:
   - All non-key attributes are fully functionally dependent on the entire Primary Key.
   - No partial dependencies exist.
3. **Third Normal Form (3NF)**:
   - No transitive dependencies exist. Non-key attributes depend solely on the primary key.
   - *Intentional Denormalization Justification*: `order_items.unit_price` stores a historical snapshot of the product price at checkout time. This prevents retrospective inflation/deflation of historical invoices when `products.price` changes, which is mandatory for financial auditability.

## 3. Concurrency Control & Isolation Strategy
- **Default Isolation Level**: `READ COMMITTED` for standard web queries.
- **Checkout & Inventory Deduction**: Execute inside transactions with `REPEATABLE READ` or explicit row-level locking (`SELECT ... FOR UPDATE`) on the `products` table to prevent overselling race conditions.
- **Optimistic Concurrency Control (OCC)**: Managed via the `version INTEGER` column across all core mutable tables (`UPDATE ... SET version = version + 1 WHERE id = :id AND version = :current_version`).

## 4. Soft Delete & Data Governance
- Critical entities utilize soft deletes (`deleted_at TIMESTAMPTZ NULL`).
- Active records are queried with `WHERE deleted_at IS NULL`.
- Enforced via partial indexes to avoid query degradation.

## 5. Security & Sensitive Data Handling
- Passwords must be hashed outside the database layer using Argon2id or Bcrypt before storage in `users.password_hash`.
- Sensitive fields (PII) are restricted via Database Role-Based Access Control (RBAC) and Row-Level Security (RLS) policies.