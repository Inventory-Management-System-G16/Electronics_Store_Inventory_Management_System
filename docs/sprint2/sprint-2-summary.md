# Sprint 2 Summary - Group 16

## Delivered

| Area | Owner | Where |
|---|---|---|
| Delete Product (confirmation page, Admin/Store Manager only) | Shreya C Rao | `/delete-product/<id>`, `tests/test_delete_product.py` |
| Duplicate Product-ID prevention (case-insensitive, database key as backstop) | Shreya C Rao | `tests/test_duplicate_id.py` |
| Numeric validation (whole numbers, price with 2 decimals, limits) | Shreya C Rao | `validate_product_fields`, `tests/test_sprint2_validation.py` |
| Mandatory-field validation with a message under each field | Shreya C Rao | `templates/add_product.html` |
| Availability Report with search and status filters | R Laksheeth | `/availability-report`, `tests/test_availability_report.py` |
| Dashboard (totals, low stock, out of stock) | R Laksheeth | `/dashboard`, `tests/test_dashboard_integration.py` |
| Inventory search, update product, availability classification | Shreyas Gowda K A | `/inventory`, `/update-product/<id>`, `tests/test_update_inventory.py` |

## Test results

See the reports in `G16-Documents/`: Unit Test Report, System Test Report and Code & Branch Coverage Report.

## Known issues

- Browser compatibility (Chrome, Firefox, Edge) and usability were checked manually only.

## Deviations from the plan

- Sprint tracking was done in GitHub (issues, milestones, pull requests), as instructed, not in Jira.
