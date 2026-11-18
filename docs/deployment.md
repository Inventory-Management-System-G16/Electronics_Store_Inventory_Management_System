# Deployment (Render + TiDB Cloud)

**Live site:** https://electronics-store-inventory-management.onrender.com/login

The app runs on a Render web service and uses a TiDB Cloud (MySQL-compatible) database. Render's free plan sleeps when idle, so the first request can take up to a minute.

## Database (one time)
1. Create a TiDB Cloud cluster and a database named `esims_db`.
2. Run the table definitions from `database/schema.sql` in the TiDB SQL editor, leaving out the first two lines (`CREATE DATABASE` and `USE`). Check with `SHOW TABLES;` that `users` and `products` exist.
3. Download the TiDB CA certificate and save it as `backend/certs/ca.pem`. It is a public certificate, so it can be committed.

TiDB does not enforce `CHECK` constraints on this plan (it shows a warning when the tables are created). The app validates the same rules, so the data stays correct.

## Environment variables
| Name | Value |
|---|---|
| `SECRET_KEY` | long random string |
| `DB_DRIVER` | `mysql` |
| `DB_HOST`, `DB_USER`, `DB_PASSWORD` | from the TiDB Connect dialog |
| `DB_PORT` | `4000` |
| `DB_NAME` | `esims_db` |
| `DB_SSL_CA` | `certs/ca.pem` |
| `COOKIE_SECURE` | `1` on Render, `0` on a local machine |

Set these in Render's Environment tab and in a local `backend/.env` file. Never commit `.env`.

## Render web service
- Repository branch: `main`
- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- Instance type: Free

After each merge into `main`, Render can redeploy automatically.

## Check the connection from your computer
From `backend/`, with `.env` filled in:
```
python check_db_connection.py
python seed_users.py
```
The first command lists the tables. The second creates the four demo accounts (see the README).

## If something fails
- Open the service's **Logs** tab in Render and read the last lines.
- A database error usually means a wrong `DB_HOST`, `DB_USER`, `DB_PASSWORD` or `DB_SSL_CA`.
- A crash about `SECRET_KEY` means that variable is missing.
