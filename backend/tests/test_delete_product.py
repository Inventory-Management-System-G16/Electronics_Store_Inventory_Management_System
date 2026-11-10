"""ESIMS-13: Delete Product (FR-INV-05 confirmation, FR-INV-06 authorization)."""
import sqlite3

import pytest


@pytest.fixture()
def product(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO products VALUES ('P100', 'HDMI Cable', 'Cables', 299.5, 20, 5, 'A1')")
    conn.commit()
    conn.close()


def count(db_path):
    conn = sqlite3.connect(db_path)
    total = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    conn.close()
    return total


# ---- authorization (FR-INV-06) ---------------------------------------------

@pytest.mark.parametrize("username", ["employee", "management"])
def test_unauthorized_roles_cannot_open_or_submit_delete(client, login_as, product, db_path, username):
    login_as(username)
    assert client.get("/delete-product/P100").status_code == 403
    assert client.post("/delete-product/P100").status_code == 403
    assert count(db_path) == 1


def test_anonymous_cannot_delete(client, product, db_path):
    response = client.post("/delete-product/P100")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
    assert count(db_path) == 1


@pytest.mark.parametrize("username", ["admin", "manager"])
def test_authorized_roles_can_open_confirmation(client, login_as, product, username):
    login_as(username)
    assert client.get("/delete-product/P100").status_code == 200


# ---- confirmation (FR-INV-05) -------------------------------------------------

def test_confirmation_page_shows_product_and_deletes_nothing(client, login_as, product, db_path):
    login_as("manager")
    html = client.get("/delete-product/P100").data
    assert b"HDMI Cable" in html and b"Yes, delete product" in html
    assert count(db_path) == 1


def test_get_never_deletes(client, login_as, product, db_path):
    login_as("admin")
    client.get("/delete-product/P100")
    assert count(db_path) == 1


# ---- behaviour --------------------------------------------------------------------

def test_confirmed_delete_removes_product_and_shows_message(client, login_as, product, db_path):
    login_as("manager")
    response = client.post("/delete-product/P100", follow_redirects=True)
    assert response.status_code == 200
    assert b"Product P100 was deleted." in response.data
    assert count(db_path) == 0
    assert b"HDMI Cable" not in response.data


def test_only_the_chosen_product_is_deleted(client, login_as, product, db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("INSERT INTO products VALUES ('P200', 'Mouse', 'Accessories', 10, 3, 1, NULL)")
    conn.commit()
    conn.close()
    login_as("admin")
    client.post("/delete-product/P100")
    conn = sqlite3.connect(db_path)
    ids = [r[0] for r in conn.execute("SELECT product_id FROM products")]
    conn.close()
    assert ids == ["P200"]


def test_unknown_product_is_404(client, login_as):
    login_as("manager")
    assert client.get("/delete-product/NOPE").status_code == 404
    assert client.post("/delete-product/NOPE").status_code == 404


def test_deleted_product_id_can_be_added_again(client, login_as, product):
    login_as("manager")
    client.post("/delete-product/P100")
    response = client.post("/add-product", data={
        "product_id": "P100", "product_name": "New", "category": "Cables",
        "price": "1", "quantity": "1", "reorder_level": "1", "location": ""})
    assert response.status_code == 302


# ---- buttons on the inventory page ---------------------------------------------------

@pytest.mark.parametrize("username,visible", [
    ("admin", True), ("manager", True), ("employee", False), ("management", False)])
def test_delete_button_visibility(client, login_as, product, username, visible):
    login_as(username)
    html = client.get("/inventory").data
    assert (b"/delete-product/P100" in html) is visible


def test_delete_failure_shows_safe_message(client, login_as, product, monkeypatch):
    import app as app_module

    real = app_module.execute

    def broken(sql, params=(), **kwargs):
        if sql.strip().upper().startswith("DELETE"):
            raise RuntimeError("secret database detail")
        return real(sql, params, **kwargs)

    monkeypatch.setattr(app_module, "execute", broken)
    login_as("manager")
    response = client.post("/delete-product/P100", follow_redirects=True)
    assert b"Could not delete the product" in response.data
    assert b"secret database detail" not in response.data
