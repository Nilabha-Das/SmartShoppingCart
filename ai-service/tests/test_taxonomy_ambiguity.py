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


def test_generic_pasta_is_ambiguous():
    data = search("pasta")

    assert data["status"] == "ambiguous"

    assert len(data["taxonomy"]["candidates"]) > 0

    assert data["products"] == []


def test_pasta_requires_clarification():
    data = search("pasta")

    response = data["response"].lower()

    assert (
        "clarif" in response
        or "which" in response
        or "choose" in response
        or "are you looking for" in response
    )