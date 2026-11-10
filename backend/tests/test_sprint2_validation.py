"""ESIMS-18 (numeric) and ESIMS-19 (mandatory fields) validation, plus restyled pages."""
import pytest

from app import validate_product_fields

VALID = {
    "product_id": "EL-001", "product_name": "USB-C Cable", "category": "Accessories",
    "price": "199.99", "quantity": "12", "reorder_level": "3", "location": "Shelf A",
}


def check(**overrides):
    return validate_product_fields({**VALID, **overrides}, new_product=True)


# ---- ESIMS-19: mandatory fields --------------------------------------------------

def test_valid_data_has_no_errors():
    assert check() == {}


@pytest.mark.parametrize("field,label", [
    ("product_id", "Product ID"), ("product_name", "Product name"),
    ("category", "Category"), ("price", "Price"),
    ("quantity", "Quantity"), ("reorder_level", "Reorder level")])
def test_each_mandatory_field_reports_its_own_message(field, label):
    assert check(**{field: ""}) == {field: f"{label} is required."}


def test_location_is_optional():
    assert check(location="") == {}


def test_all_missing_fields_are_reported_together():
    errors = validate_product_fields({}, new_product=True)
    assert set(errors) == {"product_id", "product_name", "category", "price",
                           "quantity", "reorder_level"}


# ---- ESIMS-18: numeric validation ---------------------------------------------------

@pytest.mark.parametrize("field", ["quantity", "reorder_level"])
@pytest.mark.parametrize("value,expected", [
    ("-1", "cannot be negative"), ("2.5", "whole number"), ("abc", "whole number"),
    ("1e3", "whole number"), ("1_0", "whole number"), (" 5", "whole number"),
    ("2147483648", "too large")])
def test_bad_whole_numbers(field, value, expected):
    assert expected in check(**{field: value})[field]


@pytest.mark.parametrize("field", ["quantity", "reorder_level"])
@pytest.mark.parametrize("value", ["0", "1", "2147483647"])
def test_good_whole_numbers(field, value):
    assert field not in check(**{field: value})


@pytest.mark.parametrize("value,expected", [
    ("-0.01", "cannot be negative"), ("abc", "valid number"), ("NaN", "valid number"),
    ("Infinity", "valid number"), ("1.999", "2 decimal places"),
    ("100000000", "too large")])
def test_bad_prices(value, expected):
    assert expected in check(price=value)["price"]


@pytest.mark.parametrize("value", ["0", "0.5", "10.50", "99999999.99"])
def test_good_prices(value):
    assert "price" not in check(price=value)


def test_product_id_format_and_length():
    assert "letters, numbers" in check(product_id="A/B")["product_id"]
    assert "at most 30" in check(product_id="A" * 31)["product_id"]
    assert check(product_id="A" * 30) == {}


# ---- the Add Product page shows errors next to the field ----------------------------------

def test_form_shows_error_under_the_right_field(client, login_as):
    login_as("manager")
    response = client.post("/add-product", data={**VALID, "quantity": "-4", "category": ""})
    assert response.status_code == 400
    assert b"Quantity cannot be negative." in response.data
    assert b"Category is required." in response.data
    assert b"Please correct the highlighted fields." in response.data


def test_form_keeps_typed_values_after_error(client, login_as):
    login_as("manager")
    response = client.post("/add-product", data={**VALID, "price": "-1"})
    assert b'value="USB-C Cable"' in response.data
    assert b'value="EL-001"' in response.data


def test_script_in_input_is_escaped(client, login_as):
    login_as("manager")
    response = client.post("/add-product", data={
        **VALID, "product_name": '"><script>alert(1)</script>', "price": "-1"})
    assert b"<script>alert(1)</script>" not in response.data


# ---- pages restyled for Sprint 2 still render --------------------------------------------------

def test_login_page_has_password_toggle_and_logout_message(client, login_as):
    html = client.get("/login").data
    assert b'type="password"' in html and b"pwToggle" in html
    login_as("admin")
    client.post("/logout")
    assert b"You have been logged out." in client.get("/login").data


def test_new_stylesheet_is_served(client):
    assert client.get("/static/sr-ui.css").status_code == 200
