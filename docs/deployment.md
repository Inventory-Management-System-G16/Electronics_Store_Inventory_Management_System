# Deployment (Render + TiDB Cloud)

The app runs on a Render web service and uses a TiDB Cloud (MySQL-compatible) database.

## Database
1. Create a TiDB Cloud cluster and a database named `esims_db`.
2. Run the table definitions from `database/schema.sql` (without the first two lines, `CREATE DATABASE` and `USE`).
3. Download the CA certificate and save it as `backend/certs/ca.pem`. It is a public certificate and can be committed.

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

## Render
- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`

## Check the connection locally
From `backend/`: `python check_db_connection.py`, then `python seed_users.py` to create the demo users.
