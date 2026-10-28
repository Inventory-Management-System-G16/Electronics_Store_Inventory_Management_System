import pytest


@pytest.mark.parametrize(
    "username,expected",
    [("admin", 200), ("manager", 200), ("employee", 403), ("management", 403)],
)
def test_add_product_role_permissions(client, login_as, username, expected):
    login_as(username)
    assert client.get("/add-product").status_code == expected


def test_inventory_requires_login(client):
    response = client.get("/inventory")
    assert response.status_code == 302
    assert response.headers["Location"].split("?")[0].endswith("/login")


def test_employee_cannot_post_add_product(client, login_as):
    login_as("employee")
    assert client.post("/add-product", data={}).status_code == 403
