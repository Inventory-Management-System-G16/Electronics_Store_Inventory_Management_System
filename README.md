# ESIMS - Electronics Store Inventory Management System

Group 16, Software Engineering, PES University. A Flask and MySQL web application for managing an electronics store's stock, with role-based access.

**Live site:** https://electronics-store-inventory-management.onrender.com/login

The site runs on Render's free plan, so the first load after a quiet period can take up to a minute.

## Demo accounts

| Role | Username | Password |
|---|---|---|
| Admin | `admin_demo` | `AdminDemo@123` |
| Store manager | `manager_demo` | `ManagerDemo@123` |
| Store employee | `employee_demo` | `EmployeeDemo@123` |
| Management | `management_demo` | `ManagementDemo@123` |

These are demo accounts for evaluation only. Change or delete them before the app is used for real data.

## Features

| Feature | Sprint | Owner |
|---|---|---|
| Login, logout, role-based access control, Add Product | 1 | Shreya C Rao |
| View inventory, search inventory, Update Product, availability status | 1 | Shreyas Gowda K A |
| Dashboard UI | 1 | R Laksheeth |
| Delete Product with confirmation, duplicate Product-ID prevention, numeric and mandatory field validation | 2 | Shreya C Rao |
| Availability Report with search and status filters, dashboard | 2 | R Laksheeth |
| Inventory search, update quantity and details, availability classification | 2 | Shreyas Gowda K A |

Stock status rules: **Out of Stock** when quantity is 0, **Low Stock** when quantity is greater than 0 and not above the reorder level, otherwise **In Stock**.

The system stores current quantity only. It does not keep stock-in/stock-out history (see the SRS).

## Roles

| Capability | Admin | Store manager | Store employee | Management |
|---|:---:|:---:|:---:|:---:|
| View and search inventory | Yes | Yes | Yes | Yes |
| Add product | Yes | Yes | No | No |
| Update product | Yes | Yes | Yes | No |
| Delete product | Yes | Yes | No | No |
| Availability report and dashboard | Yes | Yes | No | Yes |

Every protected route checks the role on the server with `@roles_required(...)`; hiding a button is not treated as authorization. A user without permission gets a 403 page.

## Technology

- Python 3.12, Flask 3
- MySQL (TiDB Cloud in production) through `mysql-connector-python`; SQLite for automated tests
- pytest, pytest-cov and flake8; GitHub Actions for CI
- Render for hosting, `gunicorn` as the web server

## Project layout

```
backend/
  app.py                  Flask app: routes, validation, database access
  seed_users.py           creates the demo accounts
  check_db_connection.py  checks that .env can reach the database
  templates/ static/      pages and styles
  tests/                  pytest suite (unit and route tests)
  system_tests/           end-to-end tests against a real MySQL database
  certs/ca.pem            public CA certificate for TiDB Cloud
database/schema.sql       table definitions
docs/                     sprint notes, test reports, deployment, demo script
G16-Documents/            SRS, SASD, Project Proposal, Test Plan and test reports
.github/workflows/ci.yml  lint, tests and coverage on every push
```

## Run it locally

1. Clone and enter the backend folder:
   ```powershell
   git clone https://github.com/Inventory-Management-System-G16/Electronics_Store_Inventory_Management_System.git
   cd Electronics_Store_Inventory_Management_System\backend
   ```
2. Create a virtual environment and install packages:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   Copy-Item .env.example .env
   ```
3. Edit `.env`: set `SECRET_KEY` to a long random text and fill in your MySQL details. Never commit `.env`.
4. Create the tables by running `database/schema.sql` in MySQL Workbench or the MySQL command line.
5. Create the demo accounts, then start the app:
   ```powershell
   python seed_users.py
   python app.py
   ```
6. Open http://127.0.0.1:5000/login.

To use a cloud database such as TiDB Cloud, also set `DB_PORT=4000` and `DB_SSL_CA=certs/ca.pem`. See [docs/deployment.md](docs/deployment.md).

## Testing

| Level | What it checks | Where | Command | Latest result |
|---|---|---|---|---|
| Unit and route tests | Validation functions and every route with its role rules, on a temporary SQLite database | `backend/tests/` | `pytest -q` | 159 passed |
| System tests | The whole app on a real MySQL database, checking the database after each action, plus security and timing checks | `backend/system_tests/` | `python system_tests/run_system_tests.py` | 37 of 37 passed |
| Lint | Code style | CI | `flake8 app.py seed_users.py tests --max-line-length=120 --extend-ignore=E203,W503,E501` | 0 issues |

Run the unit and route tests with coverage from `backend/`:

```powershell
pytest -q --cov=app --cov-branch --cov-report=term-missing --cov-report=html:htmlcov
```

**Coverage of `backend/app.py`** (312 statements, 118 branches), measured 17 November 2026:

| Measurement | Statements | Branches |
|---|---:|---:|
| Unit and route tests (what CI runs) | 92.9% | 88.1% |
| Plus system tests on MySQL | 95.2% | 90.7% |

The system tests delete all rows in the `users` and `products` tables of the database they run against. Use a separate test database. Instructions are at the top of `backend/system_tests/run_system_tests.py`.

More detail: [docs/test-reports/README.md](docs/test-reports/README.md).

## CI

`.github/workflows/ci.yml` runs on every push and every pull request into `main`: flake8, then pytest with branch coverage. It saves the JUnit test results and the HTML coverage report as downloadable artifacts on the run's page in the Actions tab.

## Deployment

The app runs on Render with a TiDB Cloud database. Steps and environment variables are in [docs/deployment.md](docs/deployment.md).

## Documents

| Document | File |
|---|---|
| Project Proposal | `G16-Documents/G16-Project-Proposal(final).pdf` |
| Software Requirement Specification | `G16-Documents/G16-SRS(final).pdf` |
| Software Test Plan | `G16-Documents/Software_Test_Plan_Group_16.pdf` |
| SASD | `G16-Documents/ESIMS_SASD_Group16.pdf` |
| Unit Test Report | `G16-Documents/Unit_Test_Report_Group16.pdf` |
| System Test Report | `G16-Documents/System_Test_Report_Group16.pdf` |
| Code and Branch Coverage Report | `G16-Documents/Code_and_Branch_Coverage_Report_Group16.pdf` |
| Sprint notes | `docs/sprint1/`, `docs/sprint2/` |
| Demo steps | `docs/demo-script.md` |

## Security notes

- Passwords are stored as Werkzeug hashes, never in plain text.
- Session cookies are HttpOnly and SameSite=Lax. `COOKIE_SECURE=1` is set on the deployed site, which uses HTTPS.
- All SQL uses bound parameters. The product ID is a primary key, so duplicate IDs are rejected even if two requests arrive together.
- Input is validated on the server and output is escaped by the templates.
- Keep `SECRET_KEY` and database passwords private. Rotate them if they are exposed.

## Known limitations

- No CSRF tokens on forms. This should be added before real production use.
- No user-management screen. Accounts are created with `seed_users.py`.
- No stock history, only the current quantity.
- Browser compatibility and usability were checked by hand only.

## Team

Group 16: Shreyas Gowda K A, Shreya C Rao, R Laksheeth.
