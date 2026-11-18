# Sprint 2 demo (about 2 minutes)

Use the live site https://electronics-store-inventory-management.onrender.com/login (open it a minute early, because the free plan sleeps when idle), or run locally with `python seed_users.py` and `python app.py`.

Demo accounts: `admin_demo` / `AdminDemo@123`, `manager_demo` / `ManagerDemo@123`, `employee_demo` / `EmployeeDemo@123`, `management_demo` / `ManagementDemo@123`.

1. Log in as `admin_demo`. Open Inventory, then Add Product.
2. Submit the empty form: each missing field shows its own message. (Mandatory validation)
3. Enter quantity `-1`, then `2.5`, then `abc`: each is rejected with a clear message. (Numeric validation)
4. Add a product with a new ID. Try adding the same ID again, also in a different letter case: it is rejected as a duplicate. (Duplicate ID)
5. On Inventory, click Delete on a product: a confirmation page appears and nothing is deleted yet. Confirm: the product is removed and a message is shown. (Delete)
6. Open Availability Report: filter by Low Stock and Out of Stock, and search by name. (Availability report)
7. Open Dashboard: the totals match the inventory. Update a quantity to 0 and show the Out of Stock number go up.
8. Log out. Log in as `employee_demo` and open `/dashboard`, `/add-product` and a delete URL: each shows 403. `management_demo` can open the report and dashboard but not Add or Delete. (RBAC)
9. Show the green GitHub Actions run, and the test reports in `G16-Documents/`.
