
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


def test_vegetarian_filter_does_not_claim_unverified_safety():
    data = search("vegetarian snacks")

    assert data["status"] == "dietary_unverified"
    assert data["products"] == []


def test_pork_product_not_returned_when_dietary_data_unverified():
    data = search("vegetarian high protein snacks under 300")

    assert data["status"] in {
        "dietary_unverified",
        "nutrition_unverified",
    }
    assert data["products"] == []


def test_combined_dietary_constraints_are_blocked_safely():
    data = search("vegetarian high protein snacks under 300")

    assert data["status"] in {
        "dietary_unverified",
        "nutrition_unverified",
    }
    assert data["products"] == []
