# SOFTWARE REQUIREMENTS SPECIFICATION (SRS)
## Project: Modern E-Commerce Platform (ShopPulse)
**Document Version**: 2.1.0  
**Prepared by**: Senior Business Analyst AI Agent (`ba-01`)  
**Target Roles**: System Architect (`sa-01`), Database Administrator (`dba-01`), Developer (`dev-01`)

---

## 1. Project Overview & Business Goals
ShopPulse is a high-volume omnichannel e-commerce ecosystem allowing customers to browse product catalogs, manage shopping carts, execute multi-currency checkouts, and track fulfillment shipments.

---

## 2. Functional Requirements (FR)

### [FR-01] User Registration & RBAC Authentication
- System must allow customers to register with an email and password.
- Passwords must be hashed using strong one-way cryptography.
- Supported roles: `CUSTOMER`, `STAFF`, `MANAGER`, `ADMIN`.
- System must support soft-deletion of accounts upon customer request (GDPR compliance).

### [FR-02] Product Catalog & Hierarchical Categories
- Products must belong to hierarchical categories (parent/subcategories).
- Each product possesses SKU (unique stock code), title, description, price, available inventory count, and extensible JSON metadata.
- Price must be non-negative.
- Category slugs must be URL-safe and unique.

### [FR-03] Order Placement & Composition
- A registered customer can place an order containing one or more order line items.
- Each order has an order number, status (`PENDING`, `CONFIRMED`, `PROCESSING`, `SHIPPED`, `DELIVERED`, `CANCELLED`), total amount, and shipping address.
- Each order item snapshots the unit price at purchase time to protect against subsequent product price changes.
- If an unconfirmed draft order is canceled/purged, its line items are cascaded.

### [FR-04] Payment Processing & Reconciliation
- Each order must be settled via one or more payment transactions.
- Payment supports credit card, bank transfer, VNPay, or MoMo.
- Transaction status: `UNPAID`, `AUTHORIZED`, `PAID`, `FAILED`, `REFUNDED`.
- Gateway transaction IDs must be uniquely recorded alongside raw gateway webhook payloads.

### [FR-05] Immutable Audit Trail & Compliance
- System must record audit log entries for all sensitive domain events (account state changes, price edits, order cancellations).
- Stored attributes: timestamp, actor (user_id), action type, target entity name, entity ID, JSON diff of changes, and client IP address.

---

## 3. Non-Functional Constraints for Database
- **ACID Transactions**: Checkout must be strictly atomic (stock decrement + order creation + payment record).
- **Concurrency**: Prevent overselling via row-level locks or optimistic locking.
- **Auditability**: Every table must track `created_at`, `updated_at`, `deleted_at`, and `version`.
- **Destructive Operations**: Hard deletes are forbidden on orders, users, and financial records.
