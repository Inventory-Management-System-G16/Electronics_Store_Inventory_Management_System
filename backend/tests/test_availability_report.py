"""Availability report and filtering (R Laksheeth) - TC-REP-01 to TC-REP-05."""
import sqlite3

import pytest

ROWS = [
    ("AVL-IN", "Laptop Pro", "Computers", 20, 5, "Rack A"),
    ("AVL-EDGE", "HDMI Cable", "Cables", 5, 5, "Rack B"),
    ("AVL-LOW", "USB Hub", "Accessories", 3, 5, None),
    ("AVL-OUT", "Webcam", "Accessories", 0, 5, "Rack C"),
]


@pytest.fixture()
def stocked(db_path):
    conn = sqlite3.connect(db_path)
    conn.executemany(
        "INSERT INTO products VALUES (?, ?, ?, 10, ?, ?, ?)", ROWS)
    conn.commit()
    conn.close()


@pytest.mark.parametrize("username,expected", [
    ("admin", 200), ("manager", 200), ("management", 200), ("employee", 403)])
def test_report_role_permissions(client, login_as, username, expected):
    login_as(username)
    assert client.get("/availability-report").status_code == expected


def test_report_requires_login(client):
    response = client.get("/availability-report")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_report_lists_every_product_with_its_status(client, login_as, stocked):
    login_as("manager")
    html = client.get("/availability-report").get_data(as_text=True)
    for product_id, name, *_ in ROWS:
        assert product_id in html and name in html
    assert html.count("In Stock") >= 1
    assert html.count("Low Stock") >= 2
    assert html.count("Out of Stock") >= 1


def test_report_empty_inventory_still_renders(client, login_as):
    login_as("admin")
    assert client.get("/availability-report").status_code == 200


@pytest.mark.parametrize("status,present,absent", [
    ("in_stock", ["AVL-IN"], ["AVL-EDGE", "AVL-LOW", "AVL-OUT"]),
    ("low_stock", ["AVL-EDGE", "AVL-LOW"], ["AVL-IN", "AVL-OUT"]),
    ("out_of_stock", ["AVL-OUT"], ["AVL-IN", "AVL-EDGE", "AVL-LOW"]),
])
def test_status_filter(client, login_as, stocked, status, present, absent):
    login_as("manager")
    html = client.get(f"/availability-report?status={status}").get_data(as_text=True)
    assert all(p in html for p in present)
    assert not any(a in html for a in absent)


@pytest.mark.parametrize("term,present,absent", [
    ("laptop", ["AVL-IN"], ["AVL-LOW"]),
    ("accessories", ["AVL-LOW", "AVL-OUT"], ["AVL-IN", "AVL-EDGE"]),
    ("avl-edge", ["AVL-EDGE"], ["AVL-IN", "AVL-LOW", "AVL-OUT"]),
])
def test_search_filter(client, login_as, stocked, term, present, absent):
    login_as("admin")
    html = client.get(f"/availability-report?search={term}").get_data(as_text=True)
    assert all(p in html for p in present)
    assert not any(a in html for a in absent)


def test_search_and_status_combine(client, login_as, stocked):
    login_as("admin")
    html = client.get("/availability-report?search=accessories&status=out_of_stock").get_data(as_text=True)
    assert "AVL-OUT" in html
    assert "AVL-LOW" not in html


def test_no_match_shows_empty_state(client, login_as, stocked):
    login_as("admin")
    response = client.get("/availability-report?search=zzzz-nothing")
    assert response.status_code == 200
    assert "AVL-IN" not in response.get_data(as_text=True)


def test_unknown_status_value_is_escaped(client, login_as, stocked):
    login_as("admin")
    html = client.get("/availability-report?status=<script>x</script>").get_data(as_text=True)
    assert "<script>x</script>" not in html


@pytest.mark.xfail(reason="DEF-01: template re-filters on the raw ?status= value, so an unknown "
                          "status hides every row instead of being ignored like app.py intends")
def test_unknown_status_value_is_ignored(client, login_as, stocked):
    login_as("admin")
    html = client.get("/availability-report?status=bogus").get_data(as_text=True)
    assert "AVL-IN" in html and "AVL-OUT" in html


def test_report_reflects_new_data(client, login_as, db_path):
    login_as("admin")
    assert "NEW-ITEM" not in client.get("/availability-report").get_data(as_text=True)
    conn = sqlite3.connect(db_path)
    conn.execute("INSERT INTO products VALUES ('NEW-ITEM','Fresh','Misc',1,0,2,NULL)")
    conn.commit()
    conn.close()
    assert "NEW-ITEM" in client.get("/availability-report").get_data(as_text=True)
