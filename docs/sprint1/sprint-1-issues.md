# Sprint 1 — ESIMS

**Branch:** `SG-inventory`  
**Status:** Completed (as reported by the project owner)  
**Total planned/completed story points:** 9

## Completed stories

| Jira key | Story | Points | GitHub issue | Status |
|---|---|---:|---|---|
| ESIMS-9 | View Inventory | 3 | [#11](https://github.com/Inventory-Management-System-G16/Electronics_Store_Inventory_Management_System/issues/11) | Closed |
| ESIMS-10 | Search Inventory | 3 | [#12](https://github.com/Inventory-Management-System-G16/Electronics_Store_Inventory_Management_System/issues/12) | Closed |
| ESIMS-12 | Update Product | 3 | [#13](https://github.com/Inventory-Management-System-G16/Electronics_Store_Inventory_Management_System/issues/13) | Closed |

## Implementation evidence on `SG-inventory`

- **View Inventory:** `backend/app.py` route `/inventory`; `backend/templates/inventory.html` renders inventory fields and availability status.
- **Search Inventory:** `backend/app.py` route `/inventory` supports search by Product ID, product name, and category; `backend/templates/inventory.html` provides the search selector and clear link.
- **Update Product:** `backend/app.py` route `/update-product/<product_id>` reads and updates product fields, validates numeric input, rejects negative values, and commits changes; `backend/templates/update_product.html` contains the update form.

## Burndown chart data

The sprint scope totals **9 story points**. A reliable day-by-day burndown needs the actual Sprint 1 start/end dates and daily remaining-work data or the original burndown chart. Do not infer daily progress from final issue status or commit timestamps alone.
