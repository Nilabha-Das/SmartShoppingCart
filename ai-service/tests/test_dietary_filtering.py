import json
from urllib.parse import urlencode
from urllib.request import urlopen


BASE_URL = "http://localhost:8000"


def search(message):
    params = urlencode({"message": message})
    url = f"{BASE_URL}/shopping/search?{params}"

    with urlopen(url, timeout=30) as response:
        assert response.status == 200
        return json.loads(response.read().decode("utf-8"))


def test_vegetarian_products_are_actually_vegetarian():
    data = search("vegetarian snacks")

    assert data["status"] == "resolved"

    products = data["products"]

    assert len(products) > 0

    for product in products:
        assert product["vegetarian"] is True


def test_pork_product_not_returned_as_vegetarian():
    data = search("vegetarian high protein snacks under 300")

    assert data["status"] == "resolved"

    product_ids = [
        product["product_id"]
        for product in data["products"]
    ]

    assert "P002674" not in product_ids


def test_combined_dietary_constraints():
    data = search("vegetarian high protein snacks under 300")

    assert data["status"] == "resolved"

    for product in data["products"]:
        assert product["vegetarian"] is True
        assert product["protein_g"] >= 10
        assert product["price"] <= 300