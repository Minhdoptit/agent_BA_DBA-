# USE CASES SPECIFICATION - SMART E-COMMERCE ORDER & INVENTORY SYSTEM

> **Agent ID**: `ba-01` | **Methodology**: Formal UML Use Case Specification  
> **Standard**: Alistair Cockburn Formal Template

---

## 1. Actor Catalog

| Actor Role | Classification | Description & Responsibilities |
|:---|:---:|:---|
| **Customer** | `Primary` | Main operational stakeholder for Smart E-Commerce Order & Inventory System, initiating primary workflows. |
| **System Administrator** | `Secondary / System` | Responsible for administrative governance, authorization, and system health oversight. |
| **External Service Provider** | `Secondary / System` | Third-party APIs (payment gateway, notification broker, external identity provider). |

## 2. Use Case Summary Matrix

| Use Case ID | Use Case Name | Primary Actor | Tracing FR | Postcondition Success |
|:---|:---|:---|:---:|:---|
| `UC-001` | **Execute Xay dung he thong quan ly don hang va ton kho thuong mai die** | `Customer` | `FR-001` | Business operation for [FR-001] completed successfully and audited. |
| `UC-002` | **Execute danh muc san pham (Product & Category)** | `Customer` | `FR-002` | Business operation for [FR-002] completed successfully and audited. |
| `UC-003` | **Execute gio hang (Cart)** | `Customer` | `FR-003` | Business operation for [FR-003] completed successfully and audited. |
| `UC-004` | **Execute don dat hang (Order & OrderItem)** | `Customer` | `FR-004` | Business operation for [FR-004] completed successfully and audited. |
| `UC-005` | **Execute thanh toan (Payment Transaction)** | `Customer` | `FR-005` | Business operation for [FR-005] completed successfully and audited. |
| `UC-006` | **Execute va theo doi xuat nhap kho (Inventory Transaction).** | `Customer` | `FR-006` | Business operation for [FR-006] completed successfully and audited. |

## 3. Detailed Formal Use Cases
### UC-001: Execute Xay dung he thong quan ly don hang va ton kho thuong mai die
- **Primary Actor**: `Customer`
- **Secondary Actors**: `None`
- **Trigger**: Actor initiates Xay dung he thong quan ly don hang va ton kho thuong mai die from interface.
- **Tracing Requirements**: `FR-001`

#### Preconditions:
- Actor is authenticated with valid credentials.
- Actor possesses active role permission for [FR-001].

#### Main Success Scenario (Normal Flow):
| Step | Actor Action | System Response |
|:---:|:---|:---|
| 1 | Actor navigates to the 'Xay dung he thong quan ly don hang va ton kho thuong mai die' entry point. | System verifies session authorization and presents the operational form with default parameters. |
| 2 | Actor enters required business inputs and confirms submission. | System performs synchronous schema validation on all submitted parameters. |
| 3 | Actor reviews the operation summary. | System applies business logic conforming to [FR-001], commits transaction, and logs audit record. |
| 4 | Actor receives the completion confirmation. | System displays updated status and provides reference transaction identifier. |

#### Alternative Flows:
- **Flow [2a]**: *Actor chooses to cancel or save as draft before final confirmation.*
  - System prompts actor to confirm cancellation.
  - Actor confirms; system discards or saves uncommitted draft without state mutation.
  - System routes actor back to dashboard.

#### Exception / Failure Flows:
- **Error [2b]**: *Validation fails due to missing or invalid input attributes.*
  - System intercepts invalid submission before persistent execution.
  - System highlights offending input fields with contextual error messages.
  - System retains valid entered data; actor rectifies inputs and re-submits.
- **Error [3a]**: *Downstream integration or transaction lock timeout occurs.*
  - System triggers automatic transaction rollback.
  - System logs diagnostic alert for technical operations.
  - System presents retry guidance message to actor without exposing raw stack traces.

#### Postconditions:
- **Success Guarantee**: Business operation for [FR-001] completed successfully and audited.
- **Minimal Guarantee (Failure)**: System state remains unmutated; error recorded in operational logs.

---
### UC-002: Execute danh muc san pham (Product & Category)
- **Primary Actor**: `Customer`
- **Secondary Actors**: `None`
- **Trigger**: Actor initiates danh muc san pham (Product & Category) from interface.
- **Tracing Requirements**: `FR-002`

#### Preconditions:
- Actor is authenticated with valid credentials.
- Actor possesses active role permission for [FR-002].

#### Main Success Scenario (Normal Flow):
| Step | Actor Action | System Response |
|:---:|:---|:---|
| 1 | Actor navigates to the 'danh muc san pham (Product & Category)' entry point. | System verifies session authorization and presents the operational form with default parameters. |
| 2 | Actor enters required business inputs and confirms submission. | System performs synchronous schema validation on all submitted parameters. |
| 3 | Actor reviews the operation summary. | System applies business logic conforming to [FR-002], commits transaction, and logs audit record. |
| 4 | Actor receives the completion confirmation. | System displays updated status and provides reference transaction identifier. |

#### Alternative Flows:
- **Flow [2a]**: *Actor chooses to cancel or save as draft before final confirmation.*
  - System prompts actor to confirm cancellation.
  - Actor confirms; system discards or saves uncommitted draft without state mutation.
  - System routes actor back to dashboard.

#### Exception / Failure Flows:
- **Error [2b]**: *Validation fails due to missing or invalid input attributes.*
  - System intercepts invalid submission before persistent execution.
  - System highlights offending input fields with contextual error messages.
  - System retains valid entered data; actor rectifies inputs and re-submits.
- **Error [3a]**: *Downstream integration or transaction lock timeout occurs.*
  - System triggers automatic transaction rollback.
  - System logs diagnostic alert for technical operations.
  - System presents retry guidance message to actor without exposing raw stack traces.

#### Postconditions:
- **Success Guarantee**: Business operation for [FR-002] completed successfully and audited.
- **Minimal Guarantee (Failure)**: System state remains unmutated; error recorded in operational logs.

---
### UC-003: Execute gio hang (Cart)
- **Primary Actor**: `Customer`
- **Secondary Actors**: `None`
- **Trigger**: Actor initiates gio hang (Cart) from interface.
- **Tracing Requirements**: `FR-003`

#### Preconditions:
- Actor is authenticated with valid credentials.
- Actor possesses active role permission for [FR-003].

#### Main Success Scenario (Normal Flow):
| Step | Actor Action | System Response |
|:---:|:---|:---|
| 1 | Actor navigates to the 'gio hang (Cart)' entry point. | System verifies session authorization and presents the operational form with default parameters. |
| 2 | Actor enters required business inputs and confirms submission. | System performs synchronous schema validation on all submitted parameters. |
| 3 | Actor reviews the operation summary. | System applies business logic conforming to [FR-003], commits transaction, and logs audit record. |
| 4 | Actor receives the completion confirmation. | System displays updated status and provides reference transaction identifier. |

#### Alternative Flows:
- **Flow [2a]**: *Actor chooses to cancel or save as draft before final confirmation.*
  - System prompts actor to confirm cancellation.
  - Actor confirms; system discards or saves uncommitted draft without state mutation.
  - System routes actor back to dashboard.

#### Exception / Failure Flows:
- **Error [2b]**: *Validation fails due to missing or invalid input attributes.*
  - System intercepts invalid submission before persistent execution.
  - System highlights offending input fields with contextual error messages.
  - System retains valid entered data; actor rectifies inputs and re-submits.
- **Error [3a]**: *Downstream integration or transaction lock timeout occurs.*
  - System triggers automatic transaction rollback.
  - System logs diagnostic alert for technical operations.
  - System presents retry guidance message to actor without exposing raw stack traces.

#### Postconditions:
- **Success Guarantee**: Business operation for [FR-003] completed successfully and audited.
- **Minimal Guarantee (Failure)**: System state remains unmutated; error recorded in operational logs.

---
### UC-004: Execute don dat hang (Order & OrderItem)
- **Primary Actor**: `Customer`
- **Secondary Actors**: `None`
- **Trigger**: Actor initiates don dat hang (Order & OrderItem) from interface.
- **Tracing Requirements**: `FR-004`

#### Preconditions:
- Actor is authenticated with valid credentials.
- Actor possesses active role permission for [FR-004].

#### Main Success Scenario (Normal Flow):
| Step | Actor Action | System Response |
|:---:|:---|:---|
| 1 | Actor navigates to the 'don dat hang (Order & OrderItem)' entry point. | System verifies session authorization and presents the operational form with default parameters. |
| 2 | Actor enters required business inputs and confirms submission. | System performs synchronous schema validation on all submitted parameters. |
| 3 | Actor reviews the operation summary. | System applies business logic conforming to [FR-004], commits transaction, and logs audit record. |
| 4 | Actor receives the completion confirmation. | System displays updated status and provides reference transaction identifier. |

#### Alternative Flows:
- **Flow [2a]**: *Actor chooses to cancel or save as draft before final confirmation.*
  - System prompts actor to confirm cancellation.
  - Actor confirms; system discards or saves uncommitted draft without state mutation.
  - System routes actor back to dashboard.

#### Exception / Failure Flows:
- **Error [2b]**: *Validation fails due to missing or invalid input attributes.*
  - System intercepts invalid submission before persistent execution.
  - System highlights offending input fields with contextual error messages.
  - System retains valid entered data; actor rectifies inputs and re-submits.
- **Error [3a]**: *Downstream integration or transaction lock timeout occurs.*
  - System triggers automatic transaction rollback.
  - System logs diagnostic alert for technical operations.
  - System presents retry guidance message to actor without exposing raw stack traces.

#### Postconditions:
- **Success Guarantee**: Business operation for [FR-004] completed successfully and audited.
- **Minimal Guarantee (Failure)**: System state remains unmutated; error recorded in operational logs.

---
### UC-005: Execute thanh toan (Payment Transaction)
- **Primary Actor**: `Customer`
- **Secondary Actors**: `External Service Provider`
- **Trigger**: Actor initiates thanh toan (Payment Transaction) from interface.
- **Tracing Requirements**: `FR-005`

#### Preconditions:
- Actor is authenticated with valid credentials.
- Actor possesses active role permission for [FR-005].

#### Main Success Scenario (Normal Flow):
| Step | Actor Action | System Response |
|:---:|:---|:---|
| 1 | Actor navigates to the 'thanh toan (Payment Transaction)' entry point. | System verifies session authorization and presents the operational form with default parameters. |
| 2 | Actor enters required business inputs and confirms submission. | System performs synchronous schema validation on all submitted parameters. |
| 3 | Actor reviews the operation summary. | System applies business logic conforming to [FR-005], commits transaction, and logs audit record. |
| 4 | Actor receives the completion confirmation. | System displays updated status and provides reference transaction identifier. |

#### Alternative Flows:
- **Flow [2a]**: *Actor chooses to cancel or save as draft before final confirmation.*
  - System prompts actor to confirm cancellation.
  - Actor confirms; system discards or saves uncommitted draft without state mutation.
  - System routes actor back to dashboard.

#### Exception / Failure Flows:
- **Error [2b]**: *Validation fails due to missing or invalid input attributes.*
  - System intercepts invalid submission before persistent execution.
  - System highlights offending input fields with contextual error messages.
  - System retains valid entered data; actor rectifies inputs and re-submits.
- **Error [3a]**: *Downstream integration or transaction lock timeout occurs.*
  - System triggers automatic transaction rollback.
  - System logs diagnostic alert for technical operations.
  - System presents retry guidance message to actor without exposing raw stack traces.

#### Postconditions:
- **Success Guarantee**: Business operation for [FR-005] completed successfully and audited.
- **Minimal Guarantee (Failure)**: System state remains unmutated; error recorded in operational logs.

---
### UC-006: Execute va theo doi xuat nhap kho (Inventory Transaction).
- **Primary Actor**: `Customer`
- **Secondary Actors**: `None`
- **Trigger**: Actor initiates va theo doi xuat nhap kho (Inventory Transaction). from interface.
- **Tracing Requirements**: `FR-006`

#### Preconditions:
- Actor is authenticated with valid credentials.
- Actor possesses active role permission for [FR-006].

#### Main Success Scenario (Normal Flow):
| Step | Actor Action | System Response |
|:---:|:---|:---|
| 1 | Actor navigates to the 'va theo doi xuat nhap kho (Inventory Transaction).' entry point. | System verifies session authorization and presents the operational form with default parameters. |
| 2 | Actor enters required business inputs and confirms submission. | System performs synchronous schema validation on all submitted parameters. |
| 3 | Actor reviews the operation summary. | System applies business logic conforming to [FR-006], commits transaction, and logs audit record. |
| 4 | Actor receives the completion confirmation. | System displays updated status and provides reference transaction identifier. |

#### Alternative Flows:
- **Flow [2a]**: *Actor chooses to cancel or save as draft before final confirmation.*
  - System prompts actor to confirm cancellation.
  - Actor confirms; system discards or saves uncommitted draft without state mutation.
  - System routes actor back to dashboard.

#### Exception / Failure Flows:
- **Error [2b]**: *Validation fails due to missing or invalid input attributes.*
  - System intercepts invalid submission before persistent execution.
  - System highlights offending input fields with contextual error messages.
  - System retains valid entered data; actor rectifies inputs and re-submits.
- **Error [3a]**: *Downstream integration or transaction lock timeout occurs.*
  - System triggers automatic transaction rollback.
  - System logs diagnostic alert for technical operations.
  - System presents retry guidance message to actor without exposing raw stack traces.

#### Postconditions:
- **Success Guarantee**: Business operation for [FR-006] completed successfully and audited.
- **Minimal Guarantee (Failure)**: System state remains unmutated; error recorded in operational logs.

---
*Authored by Business Analyst Agent (`ba-01`). Implementation details omitted by design.*