# Shreyas Gowda K A — ESIMS Sprint Plan

**Scope:** Only the inventory features assigned to Shreyas: View/Search Inventory, update current quantity, and automatic stock classification.  
**SRS boundary:** Current quantity only. No stock-in/stock-out transaction history.

## Sprint plan

### Sprint 1 — Completed
**Total:** 9 story points

| Story | Points | GitHub issue | Status |
|---|---:|---|---|
| View Inventory (ESIMS-9) | 3 | [#11](https://github.com/Inventory-Management-System-G16/Electronics_Store_Inventory_Management_System/issues/11) | Closed |
| Search Inventory (ESIMS-10) | 3 | [#12](https://github.com/Inventory-Management-System-G16/Electronics_Store_Inventory_Management_System/issues/12) | Closed |
| Update Product / current quantity (ESIMS-12) | 3 | [#13](https://github.com/Inventory-Management-System-G16/Electronics_Store_Inventory_Management_System/issues/13) | Closed |

### Sprint 2 — Verification and acceptance checks
**Planning estimate:** 2 story points (provisional)

| Story | GitHub issue | Status |
|---|---|---|
| Verify stock classification and quantity-update acceptance criteria | [#18](https://github.com/Inventory-Management-System-G16/Electronics_Store_Inventory_Management_System/issues/18) | Open |

Acceptance checks:
- Quantity = 0 → Out of Stock.
- Quantity > 0 and quantity <= reorder level → Low Stock.
- Quantity > reorder level → In Stock.
- Status reflects the current quantity and reorder level after an update.
- Valid updates persist; negative numeric values are rejected.
- Record test results for quantity 0, quantity equal to reorder level, and quantity one above reorder level.

## Sprint count

Plan for **2 sprints total** for this assigned scope: Sprint 1 is complete; Sprint 2 is a small verification sprint. The Sprint 2 estimate is provisional and should be adjusted if the team's estimation convention differs.

## GitHub Projects note

This file and the issues provide the sprint plan and links. The connected GitHub integration does not expose actions to create or configure GitHub Projects iterations/fields, so the actual Project board iteration assignment has not been changed. Add the listed issues to the repository's Projects board and assign the Iteration field there if your board has one.
