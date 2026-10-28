"""Tests for the integrated Update Product and Inventory (status column) features."""
import sqlite3

import pytest

VALID = {
    "product_name": "HDMI Cable", "category": "Cables", "price": "299.50",
    "quantity": "20", "reorder_level": "5", "location": "A1",
}


@pytest.fixture()
def product(db_path):
    """One product (quantity 20, reorder level 5) already in the database."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO products VALUES ('P100', 'HDMI Cable', 'Cables', 299.5, 20, 5, 'A1')")
    conn.commit()
    conn.close()


def fetch(db_path, product_id="P100"):
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT product_name, category, price, quantity, reorder_level, location "
        "FROM products WHERE product_id = ?", (product_id,)).fetchone()
    conn.close()
    return row


# ---- Update Product: access control -----------------------------------------------

def test_update_requires_login(client, product):
    response = client.get("/update-product/P100")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


@pytest.mark.parametrize("username,expected", [
    ("admin", 200), ("manager", 200), ("employee", 200), ("management", 403)])
def test_update_page_role_permissions(client, login_as, product, username, expected):
    login_as(username)
    assert client.get("/update-product/P100").status_code == expected


def test_management_cannot_post_an_update(client, login_as, product, db_path):
    login_as("management")
    response = client.post("/update-product/P100", data={**VALID, "product_name": "Hacked"})
    assert response.status_code == 403
    assert fetch(db_path)[0] == "HDMI Cable"


def test_anonymous_post_cannot_update(client, product, db_path):
    response = client.post("/update-product/P100", data={**VALID, "product_name": "Hacked"})
    assert response.status_code == 302
    assert fetch(db_path)[0] == "HDMI Cable"


# ---- Update Product: behaviour -------------------------------------------------------

def test_update_page_shows_current_values(client, login_as, product):
    login_as("manager")
    html = client.get("/update-product/P100").data
    assert b'value="HDMI Cable"' in html
    assert b'value="P100"' in html


def test_valid_update_is_saved_and_shown_in_inventory(client, login_as, product, db_path):
    login_as("manager")
    response = client.post("/update-product/P100",
                           data={**VALID, "quantity": "3", "price": "310.00"},
                           follow_redirects=True)
    assert response.status_code == 200
    assert b"Product updated successfully." in response.data
    row = fetch(db_path)
    assert row[3] == 3 and float(row[2]) == 310.0


def test_employee_can_update_quantity(client, login_as, product, db_path):
    login_as("employee")
    response = client.post("/update-product/P100", data={**VALID, "quantity": "7"})
    assert response.status_code == 302
    assert fetch(db_path)[3] == 7


def test_unknown_product_is_404(client, login_as):
    login_as("manager")
    assert client.get("/update-product/NOPE").status_code == 404
    assert client.post("/update-product/NOPE", data=VALID).status_code == 404


@pytest.mark.parametrize("overrides,message", [
    ({"quantity": "-1"}, b"cannot be negative"),
    ({"reorder_level": "-1"}, b"cannot be negative"),
    ({"price": "-5"}, b"non-negative"),
    ({"quantity": "abc"}, b"whole numbers"),
    ({"product_name": ""}, b"required fields"),
])
def test_invalid_update_is_rejected_and_not_saved(
        client, login_as, product, db_path, overrides, message):
    login_as("manager")
    response = client.post("/update-product/P100", data={**VALID, **overrides})
    assert response.status_code == 400
    assert message in response.data
    assert fetch(db_path) == ("HDMI Cable", "Cables", 299.5, 20, 5, "A1")


def test_update_form_keeps_typed_values_after_error(client, login_as, product):
    login_as("manager")
    response = client.post("/update-product/P100",
                           data={**VALID, "product_name": "New Name", "quantity": "-4"})
    assert b'value="New Name"' in response.data


def test_script_in_product_name_is_escaped(client, login_as, product):
    login_as("manager")
    response = client.post("/update-product/P100",
                           data={**VALID, "product_name": "<script>x</script>", "quantity": "-1"})
    assert b"<script>x</script>" not in response.data


# ---- Inventory page: availability status (FR-REP-01/02/03/04) ---------------------------

@pytest.mark.parametrize("quantity,reorder,label", [
    (0, 5, b"Out of Stock"),
    (1, 5, b"Low Stock"),
    (5, 5, b"Low Stock"),     # equal to reorder level -> Low Stock
    (6, 5, b"In Stock"),      # one above reorder level
    (0, 0, b"Out of Stock"),
])
def test_status_boundaries(client, login_as, db_path, quantity, reorder, label):
    conn = sqlite3.connect(db_path)
    conn.execute("INSERT INTO products VALUES ('S1', 'Item', 'Misc', 10, ?, ?, NULL)",
                 (quantity, reorder))
    conn.commit()
    conn.close()
    login_as("manager")
    assert label in client.get("/inventory").data


def test_status_changes_after_update(client, login_as, product):
    login_as("manager")
    assert b"In Stock" in client.get("/inventory").data
    client.post("/update-product/P100", data={**VALID, "quantity": "0"})
    assert b"Out of Stock" in client.get("/inventory").data


# ---- Inventory page: buttons depend on role ------------------------------------------------

@pytest.mark.parametrize("username,add_visible,update_visible", [
    ("admin", True, True), ("manager", True, True),
    ("employee", False, True), ("management", False, False)])
def test_buttons_shown_by_role(client, login_as, product, username, add_visible, update_visible):
    login_as(username)
    html = client.get("/inventory").data
    assert (b"/add-product" in html) is add_visible
    assert (b"/update-product/P100" in html) is update_visible


def test_search_still_works_with_update_button(client, login_as, product):
    login_as("manager")
    html = client.get("/inventory?search=hdmi&search_by=product_name").data
    assert b"P100" in html and b"/update-product/P100" in html


# ---- Product IDs and logout redirect (integration fixes) ---------------------------------------

@pytest.mark.parametrize("bad_id", ["A/B", "has space", "a?b", "x#y", "a;b"])
def test_new_product_id_must_be_url_safe(client, login_as, db_path, bad_id):
    login_as("manager")
    response = client.post("/add-product", data={**VALID, "product_id": bad_id})
    assert response.status_code == 400
    assert b"letters, numbers" in response.data
    conn = sqlite3.connect(db_path)
    assert conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0
    conn.close()


def test_logout_when_session_expired_does_not_set_next(client):
    response = client.post("/logout")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")  # no ?next=/logout
