"""Dashboard (R Laksheeth) working together with login, RBAC, add and update product."""
import sqlite3

import pytest

FORM = {"category": "Misc", "price": "10.00", "reorder_level": "5", "location": ""}


def add_rows(db_path, rows):
    conn = sqlite3.connect(db_path)
    conn.executemany(
        "INSERT INTO products VALUES (?, ?, 'Misc', 10, ?, ?, NULL)", rows)
    conn.commit()
    conn.close()


def metric_values(html):
    """The four numbers shown on the dashboard, in page order."""
    import re
    return [int(n) for n in re.findall(rb'class="metric-value">\s*(\d+)\s*<', html)]


@pytest.mark.parametrize("username,expected", [
    ("admin", 200), ("manager", 200), ("management", 200), ("employee", 403)])
def test_dashboard_role_permissions(client, login_as, username, expected):
    login_as(username)
    assert client.get("/dashboard").status_code == expected


def test_dashboard_requires_login(client):
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_dashboard_counts_match_inventory(client, login_as, db_path):
    add_rows(db_path, [("A", "In", 20, 5), ("B", "Low", 3, 5), ("C", "Edge", 5, 5),
                       ("D", "Out", 0, 5)])
    login_as("manager")
    # total products, total stock, low stock (3 and 5), out of stock (0)
    assert metric_values(client.get("/dashboard").data) == [4, 28, 2, 1]


def test_dashboard_updates_after_add_and_update_product(client, login_as, db_path):
    add_rows(db_path, [("A", "Item", 10, 5)])
    login_as("manager")
    assert metric_values(client.get("/dashboard").data) == [1, 10, 0, 0]

    client.post("/add-product", data={**FORM, "product_id": "B", "product_name": "New",
                                      "quantity": "0"})
    assert metric_values(client.get("/dashboard").data) == [2, 10, 0, 1]

    client.post("/update-product/A", data={**FORM, "product_name": "Item", "quantity": "2"})
    assert metric_values(client.get("/dashboard").data) == [2, 2, 1, 1]


def test_inventory_links_to_dashboard_only_for_allowed_roles(client, login_as):
    login_as("management")
    assert b'href="/dashboard"' in client.get("/inventory").data
    login_as("employee")
    assert b'href="/dashboard"' not in client.get("/inventory").data
