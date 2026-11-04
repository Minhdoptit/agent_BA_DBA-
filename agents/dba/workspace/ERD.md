# Entity-Relationship Diagram (ERD): STUDENT_MANAGEMENT_SYSTEM

> [!NOTE]
> **Database Architecture**: student_management_system | Dialect: POSTGRESQL 16+ | Designed by: DBA AI Agent (`dba-01`)

## 1. Visual ER Diagram

```mermaid
erDiagram
    CATEGORIES ||--o{ CATEGORIES : "parent_id"
    CATEGORIES ||--|{ PRODUCTS : "category_id"
    USERS ||--|{ ORDERS : "user_id"
    ORDERS ||--|{ ORDER_ITEMS : "order_id"
    PRODUCTS ||--|{ ORDER_ITEMS : "product_id"
    ORDERS ||--|{ PAYMENTS : "order_id"
    USERS ||--o{ AUDIT_LOGS : "user_id"

    USERS {
        uuid id PK "Unique surrogate primary key (UUIDv4/v7)"
        timestamptz created_at "Timestamp when record was created"
        timestamptz updated_at "Timestamp when record was last updated"
        timestamptz deleted_at "Soft-delete timestamp; NULL indicates active record"
        integer version "Optimistic locking version counter"
        varchar email UK "User primary email address"
        varchar password_hash "Argon2/Bcrypt hashed password"
        varchar full_name "Full display name"
        varchar phone_number "E.164 formatted contact phone number"
        varchar role "Security RBAC role"
        boolean is_active "Account active status flag"
    }
    CATEGORIES {
        uuid id PK "Unique surrogate primary key (UUIDv4/v7)"
        timestamptz created_at "Timestamp when record was created"
        timestamptz updated_at "Timestamp when record was last updated"
        timestamptz deleted_at "Soft-delete timestamp; NULL indicates active record"
        integer version "Optimistic locking version counter"
        uuid parent_id FK "Self-referencing parent category for nesting"
        varchar name "Category display name"
        varchar slug UK "URL-friendly identifier slug"
        text description "Category description"
    }
    PRODUCTS {
        uuid id PK "Unique surrogate primary key (UUIDv4/v7)"
        timestamptz created_at "Timestamp when record was created"
        timestamptz updated_at "Timestamp when record was last updated"
        timestamptz deleted_at "Soft-delete timestamp; NULL indicates active record"
        integer version "Optimistic locking version counter"
        uuid category_id FK "Foreign key to primary category"
        varchar sku UK "Stock Keeping Unit / Unique product code"
        varchar name "Product title"
        text description "Product detailed specifications"
        numeric price "Current unit price in default currency"
        integer stock_quantity "Available physical inventory quantity"
        jsonb metadata "Extensible dynamic attributes (dimensions, colors, specs)"
    }
    ORDERS {
        uuid id PK "Unique surrogate primary key (UUIDv4/v7)"
        timestamptz created_at "Timestamp when record was created"
        timestamptz updated_at "Timestamp when record was last updated"
        timestamptz deleted_at "Soft-delete timestamp; NULL indicates active record"
        integer version "Optimistic locking version counter"
        varchar order_number UK "Human-readable unique invoice/order number"
        uuid user_id FK "Foreign key to user who placed the order"
        varchar status "Current order state"
        numeric total_amount "Final calculated total payable amount"
        text shipping_address "Physical shipping destination details"
        text notes "Customer or fulfillment instructions"
    }
    ORDER_ITEMS {
        uuid id PK "Unique surrogate primary key (UUIDv4/v7)"
        timestamptz created_at "Timestamp when record was created"
        timestamptz updated_at "Timestamp when record was last updated"
        timestamptz deleted_at "Soft-delete timestamp; NULL indicates active record"
        integer version "Optimistic locking version counter"
        uuid order_id FK "Parent order reference"
        uuid product_id FK "Referenced catalog product"
        numeric unit_price "Historical unit price snapshot at time of purchase"
        integer quantity "Purchased unit count"
        numeric subtotal "Calculated line item subtotal (quantity * unit_price)"
    }
    PAYMENTS {
        uuid id PK "Unique surrogate primary key (UUIDv4/v7)"
        timestamptz created_at "Timestamp when record was created"
        timestamptz updated_at "Timestamp when record was last updated"
        timestamptz deleted_at "Soft-delete timestamp; NULL indicates active record"
        integer version "Optimistic locking version counter"
        uuid order_id FK "Associated order"
        varchar payment_reference UK "External payment gateway transaction reference"
        varchar payment_method "Method: CREDIT_CARD, BANK_TRANSFER, VNPAY, MOMO"
        numeric amount "Transacted monetary amount"
        varchar status "Gateway payment state"
        jsonb gateway_payload "Raw webhook/callback payload for audit trail"
    }
    AUDIT_LOGS {
        uuid id PK "Surrogate primary key"
        timestamptz created_at "Event occurrence timestamp"
        uuid user_id FK "Actor who triggered the event"
        varchar action "Action type: INSERT, UPDATE, DELETE, LOGIN, REFUND"
        varchar entity_name "Target entity name"
        varchar entity_id "Target entity identifier"
        jsonb changes "State change diff (old vs new values)"
        varchar ip_address "Client IP address"
    }
```

---

## 2. Entity Catalog & Domain Breakdown

| Entity / Table Name | Primary Key | Description | Traceability / BA Requirement |
|---|---|---|---|
| `users` | `id` | Core user accounts and authentication credentials | FR-001 |
| `categories` | `id` | Hierarchical item/service classification taxonomy | FR-01 |
| `products` | `id` | Catalog products/items offered for order or service | FR-01 |
| `orders` | `id` | Customer order headers tracking checkout transactions and lifecycle | FR-02 |
| `order_items` | `id` | Individual line items contained within an order | FR-02 |
| `payments` | `id` | Financial transaction records tied to orders | FR-03 |
| `audit_logs` | `id` | Immutable historical log of critical domain events and data alterations | FR-05 |

---

## 3. Relationship Matrix & Integrity Rules

| Parent Entity | Child Entity | Foreign Key Column | Cardinality | ON DELETE Action | Business Semantics |
|---|---|---|---|---|---|
| `categories` | `categories` | `parent_id` -> `id` | `1 : 0..N` | `SET NULL` | Child `categories` belongs to parent `categories` |
| `categories` | `products` | `category_id` -> `id` | `1 : 1..N` | `RESTRICT` | Child `products` belongs to parent `categories` |
| `users` | `orders` | `user_id` -> `id` | `1 : 1..N` | `RESTRICT` | Child `orders` belongs to parent `users` |
| `orders` | `order_items` | `order_id` -> `id` | `1 : 1..N` | `CASCADE` | Child `order_items` belongs to parent `orders` |
| `products` | `order_items` | `product_id` -> `id` | `1 : 1..N` | `RESTRICT` | Child `order_items` belongs to parent `products` |
| `orders` | `payments` | `order_id` -> `id` | `1 : 1..N` | `RESTRICT` | Child `payments` belongs to parent `orders` |
| `users` | `audit_logs` | `user_id` -> `id` | `1 : 0..N` | `SET NULL` | Child `audit_logs` belongs to parent `users` |

---

## 4. Key Design Decisions & Normalization Rationale
- **Surrogate Keys**: Standardized on UUIDv7 / UUIDv4 across all tables for distributed uniqueness and security.
- **Referential Actions**: Mission-critical master records employ `RESTRICT` to prevent accidental orphaned deletions; child composition details (e.g. line items) use `CASCADE`.
- **Audit Standard**: All tables include `created_at`, `updated_at`, `deleted_at` (soft delete), and `version`.