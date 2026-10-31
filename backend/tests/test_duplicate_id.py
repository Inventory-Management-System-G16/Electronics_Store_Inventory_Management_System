"""ESIMS-17: duplicate Product ID prevention (case-insensitive + database key)."""
import sqlite3

import app as app_module
from app import is_duplicate_key_error

VALID = {
    "product_id": "EL-001", "product_name": "USB-C Cable", "category": "Accessories",
    "price": "199.99", "quantity": "12", "reorder_level": "3", "location": "Shelf A",
}


# ---- ESIMS-17: duplicate product ID ------------------------------------------------------------

def test_duplicate_shows_message_on_product_id_field(client, login_as):
    login_as("admin")
    client.post("/add-product", data=VALID)
    response = client.post("/add-product", data=VALID)
    assert response.status_code == 409
    assert b"Product ID already exists" in response.data
    assert b'class="field has-error"' in response.data


def test_duplicate_check_ignores_letter_case(client, login_as, db_path):
    login_as("admin")
    client.post("/add-product", data=VALID)
    response = client.post("/add-product", data={**VALID, "product_id": "el-001"})
    assert response.status_code == 409
    conn = sqlite3.connect(db_path)
    assert conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 1
    conn.close()


def test_duplicate_does_not_overwrite_existing(client, login_as, db_path):
    login_as("admin")
    client.post("/add-product", data=VALID)
    client.post("/add-product", data={**VALID, "product_name": "Changed"})
    conn = sqlite3.connect(db_path)
    name = conn.execute("SELECT product_name FROM products").fetchone()[0]
    conn.close()
    assert name == "USB-C Cable"


def test_race_condition_is_caught_by_the_database_key(client, login_as, db_path, monkeypatch):
    """Pretend the pre-check found nothing; the PRIMARY KEY must still reject it."""
    login_as("admin")
    client.post("/add-product", data=VALID)
    real = app_module.execute

    def blind_precheck(sql, params=(), **kwargs):
        if "UPPER(product_id)" in sql:
            return None
        return real(sql, params, **kwargs)

    monkeypatch.setattr(app_module, "execute", blind_precheck)
    response = client.post("/add-product", data=VALID)
    assert response.status_code == 409
    assert b"Product ID already exists" in response.data


def test_other_database_errors_are_not_called_duplicates(client, login_as, monkeypatch):
    real = app_module.execute

    def broken(sql, params=(), **kwargs):
        if sql.strip().upper().startswith("INSERT"):
            raise RuntimeError("unique looking text but not a key error")
        return real(sql, params, **kwargs)

    monkeypatch.setattr(app_module, "execute", broken)
    login_as("admin")
    response = client.post("/add-product", data=VALID)
    assert response.status_code == 500
    assert b"already exists" not in response.data
    assert b"unique looking text" not in response.data


def test_is_duplicate_key_error_helper():
    assert is_duplicate_key_error(sqlite3.IntegrityError("UNIQUE constraint failed: products.product_id"))
    assert not is_duplicate_key_error(sqlite3.IntegrityError("NOT NULL constraint failed"))

    class MySQLDup(Exception):
        errno = 1062

    class MySQLOther(Exception):
        errno = 1048

    assert is_duplicate_key_error(MySQLDup())
    assert not is_duplicate_key_error(MySQLOther())
    assert not is_duplicate_key_error(ValueError("duplicate"))
