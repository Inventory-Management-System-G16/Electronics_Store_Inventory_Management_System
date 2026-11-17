# Testing: levels, results and how to run them

Results are from the run on 17-11-2026 on commit `c10a328` of `main` (plus the Add Product page layout fix and the availability report tests).

## Test levels

| Level | What it checks | Tools | Where | Run with | Result |
|---|---|---|---|---|---|
| Unit and route tests | Validation functions and each route with its role rules, on a temporary SQLite database | pytest, Flask test client | `backend/tests/` | `pytest -q` in `backend/` | 157 passed, 1 expected failure (DEF-01) |
| System | The whole app on a real MySQL-protocol database (MariaDB 10.11), checking the database after each action, plus security and timing checks | Python script | `backend/system_tests/` | `python system_tests/run_system_tests.py` in `backend/` | 37 of 37 passed |
| Lint | Code style | flake8 | CI | `flake8 app.py seed_users.py tests --max-line-length=120 --extend-ignore=E203,W503,E501` | 0 issues |

Every push and pull request runs lint and the pytest suite with coverage in GitHub Actions (`.github/workflows/ci.yml`). That is the regression testing in Test Plan section 5.

## Coverage of `backend/app.py` (312 statements, 118 branches)

| Run | Statements | Branches |
|---|---:|---:|
| Unit and route tests only (what CI runs) | 92.9% (22 missed) | 88.1% (14 missed) |
| Unit and route tests plus system tests | 95.2% (15 missed) | 90.7% (11 missed) |

Lines still not covered: 54 (test-database hook), 70 (TiDB SSL options, used only on the deployed site), 166 (defensive check), 203-206 (start-up secret-key guard), 241-244 (home page redirect), 717-719 (update-product database-error handler), 851 and 862 (legacy validator messages), 900 (`app.run`).

Reproduce: `pytest -q --cov=app --cov-branch --cov-report=term-missing --cov-report=html:htmlcov`. The HTML report is also saved by CI as the `coverage-report` artifact.

## Known defect

DEF-01 (Low): in the availability report, an unknown `?status=` value shows an empty table. `app.py` resets it to "all", but `availability_report.html` filters again on the raw URL value. It is covered by an expected-failure test.

## Not tested automatically

Browser compatibility (Chrome, Firefox, Edge) and usability. These are checked by hand during the demo.
