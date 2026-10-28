import sqlite3
import pytest

VALID = {
    "product_id": "EL-001",
    "product_name": "USB-C Cable",
    "category": "Accessories",
    "price": "199.99",
    "quantity": "12",
    "reorder_level": "3",
    "location": "Shelf A",
}


def test_add_product_persists_to_db(client, login_as, db_path):
    login_as("admin")
    response = client.post("/add-product", data=VALID)
    assert response.status_code == 302
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT product_name, quantity FROM products WHERE product_id=?",
        ("EL-001",),
    ).fetchone()
    conn.close()
    assert row == ("USB-C Cable", 12)


def test_duplicate_product_id_rejected(client, login_as):
    login_as("admin")
    client.post("/add-product", data=VALID)
    response = client.post("/add-product", data=VALID)
    assert response.status_code == 409
    assert b"Product ID already exists" in response.data


@pytest.mark.parametrize(
    "field,value",
    [
        ("product_name", ""),
        ("price", "-1"),
        ("price", "abc"),
        ("quantity", "-2"),
        ("quantity", "2.5"),
        ("reorder_level", "-1"),
        ("product_id", "x" * 31),
        ("price", "1.999"),
    ],
)
def test_invalid_product_values_rejected(client, login_as, field, value):
    login_as("manager")
    data = dict(VALID)
    data[field] = value
    assert client.post("/add-product", data=data).status_code == 400


def test_missing_required_field_rejected(client, login_as):
    login_as("admin")
    data = dict(VALID)
    data.pop("category")
    assert client.post("/add-product", data=data).status_code == 400


def test_optional_location_can_be_blank(client, login_as):
    login_as("manager")
    data = dict(VALID)
    data["product_id"] = "EL-002"
    data["location"] = ""
    assert client.post("/add-product", data=data).status_code == 302


def test_sql_injection_string_is_treated_as_data(client, login_as, db_path):
    login_as("admin")
    data = dict(VALID)
    data["product_id"] = "EL-003"
    data["product_name"] = "Cable'); DROP TABLE products;--"
    assert client.post("/add-product", data=data).status_code == 302
    conn = sqlite3.connect(db_path)
    assert conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 1
    conn.close()
