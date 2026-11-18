"""Smoke checks for core application routes using the isolated test database."""


def test_login_page_loads(client):
    assert client.get("/login").status_code == 200


def test_inventory_requires_login(client):
    response = client.get("/inventory")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_authenticated_core_pages(client, login_as):
    assert login_as("admin").status_code == 302
    for path in ("/inventory", "/dashboard", "/availability-report"):
        assert client.get(path).status_code == 200
    assert client.post("/logout").status_code == 302
    assert client.get("/inventory").status_code == 302
