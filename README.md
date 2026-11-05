# ESIMS - Electronics Store Inventory Management System (Group 16)

Flask + MySQL web application. Current quantity only; no stock-in/stock-out history (see SRS).

## Sprint 1 features

| Feature | Owner |
|---|---|
| Login, Logout, Role-Based Access Control, Add Product | Shreya C Rao |
| View Inventory, Search Inventory, Update Product, availability status | Shreyas Gowda K A |
| Dashboard UI | R Laksheeth |

Sprint planning notes for the inventory scope are in `docs/sprint1/`.

## 1. Get the code

```bash
git clone https://github.com/Inventory-Management-System-G16/Electronics_Store_Inventory_Management_System.git
cd Electronics_Store_Inventory_Management_System
git switch main
```

Keep `G16-Documents/` and `docs/` untouched when adding code.

## 2. Python setup

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` with your local values. Set `SECRET_KEY` to a long random secret. Do not commit `.env`. The sample `.env.example` uses an application DB account; for local setup you may use your own MySQL user.

Create tables in MySQL Workbench or the MySQL CLI by running `database/schema.sql`. If you run it from the repository root, use the SQL file path there. Ensure the `products` table columns match the existing teammate inventory code (`product_id`, `product_name`, `category`, `price`, `quantity`, `reorder_level`, `location`).

Create demo accounts for local development only:

```powershell
python seed_users.py
```

This generates random one-time passwords and prints them in the terminal. Do not use demo users in production. Never hardcode or commit real passwords.

Start the app:

```powershell
python app.py
```

Browse to `http://127.0.0.1:5000/login`.

## 3. Role policy

| Capability | Admin | Store manager | Store employee | Management |
|---|---:|---:|---:|---:|
| View/search inventory | Yes | Yes | Yes | Yes |
| Add product | Yes | Yes | No | No |
| Update product | Yes | Yes | Yes | No |
| Delete product | Yes | Yes | No | No |
| Reports/dashboard | Yes | Yes | No | Yes |
| Manage users/settings | Yes | No | No | No |

Implemented so far: login, logout, inventory view/search, Add Product and Update Product. Routes use the `ADD_ROLES` / `UPDATE_ROLES` constants in `backend/app.py`; add `@roles_required(...)` to every new protected route, because hiding buttons is not authorization.

## 4. Tests

Tests use a temporary SQLite database so they don't modify your MySQL development database:

```powershell
cd backend
pytest -v
flake8 app.py seed_users.py tests --max-line-length=120 --extend-ignore=E203,W503,E501
```

Test coverage includes valid/invalid login, inactive accounts, session logout, access permissions, missing fields, negative and malformed numbers, duplicate product IDs, optional location and SQL-injection-shaped input. MySQL integration should also be tested manually against the team's actual schema before merging.

## 5. Git commits

Stage specific files for each commit, after verifying `git diff`. Suggested logical commits:

```bash
git add backend/app.py backend/templates/login.html backend/tests/test_auth.py
git commit -m "feat(ESIMS-6): implement secure login"

git add backend/app.py backend/tests/test_rbac.py backend/templates/403.html
git commit -m "feat(ESIMS-7): implement role-based access control"

git add backend/app.py backend/templates/login.html backend/templates/inventory.html backend/templates/add_product.html backend/tests/test_auth.py
git commit -m "feat(ESIMS-8): implement secure logout"

git add backend/app.py backend/templates/add_product.html backend/tests/test_add_product.py backend/tests/test_validators.py database/schema.sql
 git commit -m "feat(ESIMS-11): implement add product validation"

git add .github/workflows/ci.yml .gitignore backend/requirements.txt README.md
 git commit -m "ci: add Sprint 1 automated tests"

git status
git push -u origin feature/shreya-sprint1
```

These are examples, not commands to paste blindly: the same file may contain changes for multiple tasks. For clean commits, stage hunks with `git add -p` or finish one task at a time and run `git diff --cached` before each commit. Do not commit `.env`, `.venv/`, local DB files, or secrets.

## 6. GitHub Actions

`.github/workflows/ci.yml` runs lint and tests on pushes and pull requests. Push your branch, open the repository's Actions tab and verify the run is green. CI passing does not replace a manual test against MySQL or review of integration with the teammate's routes.

## Security notes

- Passwords are verified using Werkzeug password hashes; they are never stored in plaintext.
- Session cookies are HttpOnly and SameSite=Lax; set `COOKIE_SECURE=1` when deployed over HTTPS.
- Keep `SECRET_KEY` private and rotate it if exposed.
- SQL uses bound parameters; product ID is a primary key, preventing duplicate IDs even if concurrent requests race.
- Use HTTPS in deployment, add CSRF protection for state-changing forms before production, and never expose stack traces or DB credentials to users.
