from app import validate_product

VALID = {
    "product_id": "P-1",
    "product_name": "Cable",
    "category": "Accessories",
    "price": "1.00",
    "quantity": "0",
    "reorder_level": "0",
    "location": "",
}


def test_valid_product():
    assert validate_product(VALID) is None


def test_zero_values_are_allowed():
    assert validate_product(VALID) is None


def test_missing_required_value():
    data = dict(VALID)
    data["product_id"] = ""
    assert validate_product(data)
