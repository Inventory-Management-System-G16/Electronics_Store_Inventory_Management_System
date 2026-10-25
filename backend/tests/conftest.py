import os
import sqlite3
import tempfile
import pytest
from app import create_app
from werkzeug.security import generate_password_hash

SCHEMA = """
CREATE TABLE users (
 user_id INTEGER PRIMARY KEY AUTOINCREMENT,
 username TEXT NOT NULL UNIQUE,
 email TEXT NOT NULL UNIQUE,
 password_hash TEXT NOT NULL,
 role TEXT NOT NULL,
 is_active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE products (
 product_id TEXT PRIMARY KEY,
 product_name TEXT NOT NULL,
 category TEXT NOT NULL,
 price NUMERIC NOT NULL,
 quantity INTEGER NOT NULL,
 reorder_level INTEGER NOT NULL,
 location TEXT
);

"""


@pytest.fixture()
def app():
    fd, path = tempfile.mkstemp(suffix=".sqlite3")
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    users = [
        ("admin", "admin@test.local", "admin", 1),
        ("manager", "manager@test.local", "store_manager", 1),
        ("employee", "employee@test.local", "store_employee", 1),
        ("management", "management@test.local", "management", 1),
        ("inactive", "inactive@test.local", "admin", 0),
    ]
    for username, email, role, active in users:
        conn.execute(
            "INSERT INTO users "
            "(username,email,password_hash,role,is_active) "
            "VALUES(?,?,?,?,?)",
            (
                username,
                email,
                generate_password_hash("CorrectPass!23"),
                role,
                active,
            ),
        )
    conn.commit()
    conn.close()
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DB_DRIVER": "sqlite",
            "SQLITE_PATH": path,
        }
    )
    yield app
    os.unlink(path)


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db_path(app):
    return app.config["SQLITE_PATH"]


@pytest.fixture()
def login_as(client):
    def _login(username, password="CorrectPass!23"):
        return client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=False,
        )

    return _login
