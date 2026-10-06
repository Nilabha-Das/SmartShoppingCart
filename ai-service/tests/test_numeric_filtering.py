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


def test_high_protein_filter():
    data = search("protein snacks")

    assert data["status"] == "resolved"
    assert len(data["products"]) > 0

    for product in data["products"]:
        assert product["protein_g"] >= 10


def test_max_price_filter():
    data = search("snacks under 300")

    assert data["status"] == "resolved"
    assert len(data["products"]) > 0

    for product in data["products"]:
        assert product["price"] <= 300


def test_combined_price_and_protein_filter():
    data = search("high protein snacks under 300")

    assert data["status"] == "resolved"
    assert len(data["products"]) > 0

    for product in data["products"]:
        assert product["protein_g"] >= 10
        assert product["price"] <= 300