# Data Requirements Specification: STUDENT_MANAGEMENT_SYSTEM

> [!NOTE]
> **Document Version**: 1.0.0 | **Author**: Senior Database Architect (`dba-01`)
> **Source Requirement**: Business Analyst Specification (Student Management System)

## 1. Executive Summary & Data Architecture Scope
This document details the data requirements, entity definitions, attribute domains, and validation rules derived directly from the business specifications provided by Business Analyst AI Agent (`ba-01`).
The data model strictly implements **Third Normal Form (3NF)** with explicit, documented denormalizations for historical transaction stability.

---

## 2. Business Entity Catalog & Domain Definitions

| Entity Name | Storage Table | Classification | Estimated Growth (1 Year) | Retention Policy |
|---|---|---|---|---|
| User Account | `users` | Core Master | 50,000 - 200,000 rows | Indefinite (Soft-delete only) |
| Category Hierarchy | `categories` | Reference Taxonomy | < 1,000 rows | Indefinite |
| Product Catalog | `products` | Master Data | 10,000 - 50,000 rows | Indefinite |
| Order Header | `orders` | Transactional | 500,000 - 2,000,000 rows | 5 Years Active; Cold Archive 10 Years |
| Order Line Item | `order_items` | Transactional (Composition) | 2,000,000 - 8,000,000 rows | Inherits Order Policy |
| Payment Transaction | `payments` | Financial Audit | 500,000 - 2,000,000 rows | 10 Years Legal Compliance |
| Audit & Activity Log | `audit_logs` | Immutable Compliance | 10,000,000+ rows | 2 Years Active; S3 Parquet 7 Years |

---

## 3. Data Dictionary & Attribute Specifications

### Entity: `users` (Core user accounts and authentication credentials)

| Column Name | Physical Data Type | Nullable | Primary / Unique | Check Constraint | Business Definition & Comments |
|---|---|---|---|---|---|
| `id` | `UUID` | NO | **PK** | - | Unique surrogate primary key (UUIDv4/v7) |
| `created_at` | `TIMESTAMPTZ` | NO | **-** | - | Timestamp when record was created |
| `updated_at` | `TIMESTAMPTZ` | NO | **-** | - | Timestamp when record was last updated |
| `deleted_at` | `TIMESTAMPTZ` | YES | **-** | - | Soft-delete timestamp; NULL indicates active record |
| `version` | `INTEGER` | NO | **-** | - | Optimistic locking version counter |
| `email` | `VARCHAR(255)` | NO | **UK** | - | User primary email address |
| `password_hash` | `VARCHAR(255)` | NO | **-** | - | Argon2/Bcrypt hashed password |
| `full_name` | `VARCHAR(150)` | NO | **-** | - | Full display name |
| `phone_number` | `VARCHAR(30)` | YES | **-** | - | E.164 formatted contact phone number |
| `role` | `VARCHAR(50)` | NO | **-** | `role IN ('ADMIN', 'CUSTOMER', 'STAFF', 'MANAGER')` | Security RBAC role |
| `is_active` | `BOOLEAN` | NO | **-** | - | Account active status flag |

### Entity: `categories` (Hierarchical item/service classification taxonomy)

| Column Name | Physical Data Type | Nullable | Primary / Unique | Check Constraint | Business Definition & Comments |
|---|---|---|---|---|---|
| `id` | `UUID` | NO | **PK** | - | Unique surrogate primary key (UUIDv4/v7) |
| `created_at` | `TIMESTAMPTZ` | NO | **-** | - | Timestamp when record was created |
| `updated_at` | `TIMESTAMPTZ` | NO | **-** | - | Timestamp when record was last updated |
| `deleted_at` | `TIMESTAMPTZ` | YES | **-** | - | Soft-delete timestamp; NULL indicates active record |
| `version` | `INTEGER` | NO | **-** | - | Optimistic locking version counter |
| `parent_id` | `UUID` | YES | **-** | - | Self-referencing parent category for nesting |
| `name` | `VARCHAR(100)` | NO | **-** | - | Category display name |
| `slug` | `VARCHAR(120)` | NO | **UK** | - | URL-friendly identifier slug |
| `description` | `TEXT` | YES | **-** | - | Category description |

### Entity: `products` (Catalog products/items offered for order or service)

| Column Name | Physical Data Type | Nullable | Primary / Unique | Check Constraint | Business Definition & Comments |
|---|---|---|---|---|---|
| `id` | `UUID` | NO | **PK** | - | Unique surrogate primary key (UUIDv4/v7) |
| `created_at` | `TIMESTAMPTZ` | NO | **-** | - | Timestamp when record was created |
| `updated_at` | `TIMESTAMPTZ` | NO | **-** | - | Timestamp when record was last updated |
| `deleted_at` | `TIMESTAMPTZ` | YES | **-** | - | Soft-delete timestamp; NULL indicates active record |
| `version` | `INTEGER` | NO | **-** | - | Optimistic locking version counter |
| `category_id` | `UUID` | NO | **-** | - | Foreign key to primary category |
| `sku` | `VARCHAR(64)` | NO | **UK** | - | Stock Keeping Unit / Unique product code |
| `name` | `VARCHAR(200)` | NO | **-** | - | Product title |
| `description` | `TEXT` | YES | **-** | - | Product detailed specifications |
| `price` | `NUMERIC(12, 2)` | NO | **-** | `price >= 0` | Current unit price in default currency |
| `stock_quantity` | `INTEGER` | NO | **-** | `stock_quantity >= 0` | Available physical inventory quantity |
| `metadata` | `JSONB` | YES | **-** | - | Extensible dynamic attributes (dimensions, colors, specs) |

### Entity: `orders` (Customer order headers tracking checkout transactions and lifecycle)

| Column Name | Physical Data Type | Nullable | Primary / Unique | Check Constraint | Business Definition & Comments |
|---|---|---|---|---|---|
| `id` | `UUID` | NO | **PK** | - | Unique surrogate primary key (UUIDv4/v7) |
| `created_at` | `TIMESTAMPTZ` | NO | **-** | - | Timestamp when record was created |
| `updated_at` | `TIMESTAMPTZ` | NO | **-** | - | Timestamp when record was last updated |
| `deleted_at` | `TIMESTAMPTZ` | YES | **-** | - | Soft-delete timestamp; NULL indicates active record |
| `version` | `INTEGER` | NO | **-** | - | Optimistic locking version counter |
| `order_number` | `VARCHAR(50)` | NO | **UK** | - | Human-readable unique invoice/order number |
| `user_id` | `UUID` | NO | **-** | - | Foreign key to user who placed the order |
| `status` | `VARCHAR(30)` | NO | **-** | `status IN ('PENDING', 'CONFIRMED', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED')` | Current order state |
| `total_amount` | `NUMERIC(14, 2)` | NO | **-** | `total_amount >= 0` | Final calculated total payable amount |
| `shipping_address` | `TEXT` | NO | **-** | - | Physical shipping destination details |
| `notes` | `TEXT` | YES | **-** | - | Customer or fulfillment instructions |

### Entity: `order_items` (Individual line items contained within an order)

| Column Name | Physical Data Type | Nullable | Primary / Unique | Check Constraint | Business Definition & Comments |
|---|---|---|---|---|---|
| `id` | `UUID` | NO | **PK** | - | Unique surrogate primary key (UUIDv4/v7) |
| `created_at` | `TIMESTAMPTZ` | NO | **-** | - | Timestamp when record was created |
| `updated_at` | `TIMESTAMPTZ` | NO | **-** | - | Timestamp when record was last updated |
| `deleted_at` | `TIMESTAMPTZ` | YES | **-** | - | Soft-delete timestamp; NULL indicates active record |
| `version` | `INTEGER` | NO | **-** | - | Optimistic locking version counter |
| `order_id` | `UUID` | NO | **-** | - | Parent order reference |
| `product_id` | `UUID` | NO | **-** | - | Referenced catalog product |
| `unit_price` | `NUMERIC(12, 2)` | NO | **-** | `unit_price >= 0` | Historical unit price snapshot at time of purchase |
| `quantity` | `INTEGER` | NO | **-** | `quantity > 0` | Purchased unit count |
| `subtotal` | `NUMERIC(14, 2)` | NO | **-** | `subtotal >= 0` | Calculated line item subtotal (quantity * unit_price) |

### Entity: `payments` (Financial transaction records tied to orders)

| Column Name | Physical Data Type | Nullable | Primary / Unique | Check Constraint | Business Definition & Comments |
|---|---|---|---|---|---|
| `id` | `UUID` | NO | **PK** | - | Unique surrogate primary key (UUIDv4/v7) |
| `created_at` | `TIMESTAMPTZ` | NO | **-** | - | Timestamp when record was created |
| `updated_at` | `TIMESTAMPTZ` | NO | **-** | - | Timestamp when record was last updated |
| `deleted_at` | `TIMESTAMPTZ` | YES | **-** | - | Soft-delete timestamp; NULL indicates active record |
| `version` | `INTEGER` | NO | **-** | - | Optimistic locking version counter |
| `order_id` | `UUID` | NO | **-** | - | Associated order |
| `payment_reference` | `VARCHAR(100)` | NO | **UK** | - | External payment gateway transaction reference |
| `payment_method` | `VARCHAR(50)` | NO | **-** | - | Method: CREDIT_CARD, BANK_TRANSFER, VNPAY, MOMO |
| `amount` | `NUMERIC(14, 2)` | NO | **-** | `amount > 0` | Transacted monetary amount |
| `status` | `VARCHAR(30)` | NO | **-** | `status IN ('UNPAID', 'AUTHORIZED', 'PAID', 'FAILED', 'REFUNDED')` | Gateway payment state |
| `gateway_payload` | `JSONB` | YES | **-** | - | Raw webhook/callback payload for audit trail |

### Entity: `audit_logs` (Immutable historical log of critical domain events and data alterations)

| Column Name | Physical Data Type | Nullable | Primary / Unique | Check Constraint | Business Definition & Comments |
|---|---|---|---|---|---|
| `id` | `UUID` | NO | **PK** | - | Surrogate primary key |
| `created_at` | `TIMESTAMPTZ` | NO | **-** | - | Event occurrence timestamp |
| `user_id` | `UUID` | YES | **-** | - | Actor who triggered the event |
| `action` | `VARCHAR(100)` | NO | **-** | - | Action type: INSERT, UPDATE, DELETE, LOGIN, REFUND |
| `entity_name` | `VARCHAR(100)` | NO | **-** | - | Target entity name |
| `entity_id` | `VARCHAR(100)` | NO | **-** | - | Target entity identifier |
| `changes` | `JSONB` | YES | **-** | - | State change diff (old vs new values) |
| `ip_address` | `VARCHAR(45)` | YES | **-** | - | Client IP address |

---

## 4. Referential Integrity & Deletion Rules
- **Master Entities (`users`, `products`, `orders`)**: Protected by `ON DELETE RESTRICT`. Master records with active dependencies cannot be deleted directly.
- **Composition Entities (`order_items`)**: Bound to parent `orders` with `ON DELETE CASCADE`. If a transient draft order is purged, its line items are cleaned up automatically.
- **Audit Entities (`audit_logs`)**: Strictly append-only. References to deleted users are decoupled via `ON DELETE SET NULL` to preserve historical event integrity.