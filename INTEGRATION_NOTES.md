# Integration notes for the team

1. Start from `main` in your own feature branch, as requested. The uploaded main snapshot has documents only; the uploaded `SG-inventory` snapshot has the teammate's inventory app.
2. This implementation puts routes in a Flask app factory for clarity. The teammate currently keeps routes in one `backend/app.py`; when the branches are combined, do a deliberate code review and merge routes/connection helpers. Do not blindly replace the teammate's `app.py`.
3. Remove the hardcoded database password from the teammate's code and move connection settings to environment variables before merging.
4. Confirm the exact `users` schema and `products` schema with the team. `database/schema.sql` creates a `users` table and the expected product columns, but do not run destructive schema changes against a shared DB.
5. The RBAC policy is grounded in the project proposal/SRS and is applied to routes in this starter. When adding protection to the teammate's update route, the current proposal ownership says the employee can perform permitted routine operations; confirm the final permission matrix with the team before choosing the decorator for update/delete.
6. This is a starter code bundle. Run the tests locally and validate with MySQL before declaring the Jira tasks Done. The test runner in the generation environment did not have Flask installed, so no successful test run is claimed here.
