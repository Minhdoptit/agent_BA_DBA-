# USE CASES SPECIFICATION - WAREHOUSE INVENTORY MANAGEMENT

> **Agent ID**: `ba-01` | **Methodology**: Formal UML Use Case Specification  
> **Standard**: Alistair Cockburn Formal Template

---

## 1. Actor Catalog

| Actor Role | Classification | Description & Responsibilities |
|:---|:---:|:---|
| **Customer** | `Primary` | Main operational stakeholder for Warehouse Inventory Management, initiating primary workflows. |
| **System Administrator** | `Secondary / System` | Responsible for administrative governance, authorization, and system health oversight. |
| **External Service Provider** | `Secondary / System` | Third-party APIs (payment gateway, notification broker, external identity provider). |

## 2. Use Case Summary Matrix

| Use Case ID | Use Case Name | Primary Actor | Tracing FR | Postcondition Success |
|:---|:---|:---|:---:|:---|
| `UC-001` | **Execute Hệ thống quản lý kho thông minh cho chuỗi bán lẻ** | `System Administrator` | `FR-001` | Business operation for [FR-001] completed successfully and audited. |
| `UC-002` | **Execute Nhập kho** | `Customer` | `FR-002` | Business operation for [FR-002] completed successfully and audited. |
| `UC-003` | **Execute xuất kho** | `Customer` | `FR-003` | Business operation for [FR-003] completed successfully and audited. |
| `UC-004` | **Execute kiểm kê định kỳ với mã vạch QR code.** | `Customer` | `FR-004` | Business operation for [FR-004] completed successfully and audited. |
| `UC-005` | **Execute Cảnh báo tồn kho tối thiểu và tự động đề xuất đơn đặt hàng m** | `Customer` | `FR-005` | Business operation for [FR-005] completed successfully and audited. |
| `UC-006` | **Execute Phân quyền cho Thủ kho** | `Customer` | `FR-006` | Business operation for [FR-006] completed successfully and audited. |
| `UC-007` | **Execute Nhân viên bốc dỡ** | `Customer` | `FR-007` | Business operation for [FR-007] completed successfully and audited. |
| `UC-008` | **Execute và Quản lý logistics.** | `System Administrator` | `FR-008` | Business operation for [FR-008] completed successfully and audited. |
| `UC-009` | **Execute Báo cáo doanh số và tỷ lệ thất thoát theo tháng.** | `Customer` | `FR-009` | Business operation for [FR-009] completed successfully and audited. |

## 3. Detailed Formal Use Cases
### UC-001: Execute Hệ thống quản lý kho thông minh cho chuỗi bán lẻ
- **Primary Actor**: `System Administrator`
- **Secondary Actors**: `None`
- **Trigger**: Actor initiates Hệ thống quản lý kho thông minh cho chuỗi bán lẻ from interface.
- **Tracing Requirements**: `FR-001`

#### Preconditions:
- Actor is authenticated with valid credentials.
- Actor possesses active role permission for [FR-001].

#### Main Success Scenario (Normal Flow):
| Step | Actor Action | System Response |
|:---:|:---|:---|
| 1 | Actor navigates to the 'Hệ thống quản lý kho thông minh cho chuỗi bán lẻ' entry point. | System verifies session authorization and presents the operational form with default parameters. |
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
### UC-002: Execute Nhập kho
- **Primary Actor**: `Customer`
- **Secondary Actors**: `None`
- **Trigger**: Actor initiates Nhập kho from interface.
- **Tracing Requirements**: `FR-002`

#### Preconditions:
- Actor is authenticated with valid credentials.
- Actor possesses active role permission for [FR-002].

#### Main Success Scenario (Normal Flow):
| Step | Actor Action | System Response |
|:---:|:---|:---|
| 1 | Actor navigates to the 'Nhập kho' entry point. | System verifies session authorization and presents the operational form with default parameters. |
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
### UC-003: Execute xuất kho
- **Primary Actor**: `Customer`
- **Secondary Actors**: `None`
- **Trigger**: Actor initiates xuất kho from interface.
- **Tracing Requirements**: `FR-003`

#### Preconditions:
- Actor is authenticated with valid credentials.
- Actor possesses active role permission for [FR-003].

#### Main Success Scenario (Normal Flow):
| Step | Actor Action | System Response |
|:---:|:---|:---|
| 1 | Actor navigates to the 'xuất kho' entry point. | System verifies session authorization and presents the operational form with default parameters. |
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
### UC-004: Execute kiểm kê định kỳ với mã vạch QR code.
- **Primary Actor**: `Customer`
- **Secondary Actors**: `None`
- **Trigger**: Actor initiates kiểm kê định kỳ với mã vạch QR code. from interface.
- **Tracing Requirements**: `FR-004`

#### Preconditions:
- Actor is authenticated with valid credentials.
- Actor possesses active role permission for [FR-004].

#### Main Success Scenario (Normal Flow):
| Step | Actor Action | System Response |
|:---:|:---|:---|
| 1 | Actor navigates to the 'kiểm kê định kỳ với mã vạch QR code.' entry point. | System verifies session authorization and presents the operational form with default parameters. |
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
### UC-005: Execute Cảnh báo tồn kho tối thiểu và tự động đề xuất đơn đặt hàng m
- **Primary Actor**: `Customer`
- **Secondary Actors**: `None`
- **Trigger**: Actor initiates Cảnh báo tồn kho tối thiểu và tự động đề xuất đơn đặt hàng m from interface.
- **Tracing Requirements**: `FR-005`

#### Preconditions:
- Actor is authenticated with valid credentials.
- Actor possesses active role permission for [FR-005].

#### Main Success Scenario (Normal Flow):
| Step | Actor Action | System Response |
|:---:|:---|:---|
| 1 | Actor navigates to the 'Cảnh báo tồn kho tối thiểu và tự động đề xuất đơn đặt hàng m' entry point. | System verifies session authorization and presents the operational form with default parameters. |
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
### UC-006: Execute Phân quyền cho Thủ kho
- **Primary Actor**: `Customer`
- **Secondary Actors**: `None`
- **Trigger**: Actor initiates Phân quyền cho Thủ kho from interface.
- **Tracing Requirements**: `FR-006`

#### Preconditions:
- Actor is authenticated with valid credentials.
- Actor possesses active role permission for [FR-006].

#### Main Success Scenario (Normal Flow):
| Step | Actor Action | System Response |
|:---:|:---|:---|
| 1 | Actor navigates to the 'Phân quyền cho Thủ kho' entry point. | System verifies session authorization and presents the operational form with default parameters. |
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
### UC-007: Execute Nhân viên bốc dỡ
- **Primary Actor**: `Customer`
- **Secondary Actors**: `None`
- **Trigger**: Actor initiates Nhân viên bốc dỡ from interface.
- **Tracing Requirements**: `FR-007`

#### Preconditions:
- Actor is authenticated with valid credentials.
- Actor possesses active role permission for [FR-007].

#### Main Success Scenario (Normal Flow):
| Step | Actor Action | System Response |
|:---:|:---|:---|
| 1 | Actor navigates to the 'Nhân viên bốc dỡ' entry point. | System verifies session authorization and presents the operational form with default parameters. |
| 2 | Actor enters required business inputs and confirms submission. | System performs synchronous schema validation on all submitted parameters. |
| 3 | Actor reviews the operation summary. | System applies business logic conforming to [FR-007], commits transaction, and logs audit record. |
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
- **Success Guarantee**: Business operation for [FR-007] completed successfully and audited.
- **Minimal Guarantee (Failure)**: System state remains unmutated; error recorded in operational logs.

---
### UC-008: Execute và Quản lý logistics.
- **Primary Actor**: `System Administrator`
- **Secondary Actors**: `None`
- **Trigger**: Actor initiates và Quản lý logistics. from interface.
- **Tracing Requirements**: `FR-008`

#### Preconditions:
- Actor is authenticated with valid credentials.
- Actor possesses active role permission for [FR-008].

#### Main Success Scenario (Normal Flow):
| Step | Actor Action | System Response |
|:---:|:---|:---|
| 1 | Actor navigates to the 'và Quản lý logistics.' entry point. | System verifies session authorization and presents the operational form with default parameters. |
| 2 | Actor enters required business inputs and confirms submission. | System performs synchronous schema validation on all submitted parameters. |
| 3 | Actor reviews the operation summary. | System applies business logic conforming to [FR-008], commits transaction, and logs audit record. |
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
- **Success Guarantee**: Business operation for [FR-008] completed successfully and audited.
- **Minimal Guarantee (Failure)**: System state remains unmutated; error recorded in operational logs.

---
### UC-009: Execute Báo cáo doanh số và tỷ lệ thất thoát theo tháng.
- **Primary Actor**: `Customer`
- **Secondary Actors**: `None`
- **Trigger**: Actor initiates Báo cáo doanh số và tỷ lệ thất thoát theo tháng. from interface.
- **Tracing Requirements**: `FR-009`

#### Preconditions:
- Actor is authenticated with valid credentials.
- Actor possesses active role permission for [FR-009].

#### Main Success Scenario (Normal Flow):
| Step | Actor Action | System Response |
|:---:|:---|:---|
| 1 | Actor navigates to the 'Báo cáo doanh số và tỷ lệ thất thoát theo tháng.' entry point. | System verifies session authorization and presents the operational form with default parameters. |
| 2 | Actor enters required business inputs and confirms submission. | System performs synchronous schema validation on all submitted parameters. |
| 3 | Actor reviews the operation summary. | System applies business logic conforming to [FR-009], commits transaction, and logs audit record. |
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
- **Success Guarantee**: Business operation for [FR-009] completed successfully and audited.
- **Minimal Guarantee (Failure)**: System state remains unmutated; error recorded in operational logs.

---
*Authored by Business Analyst Agent (`ba-01`). Implementation details omitted by design.*