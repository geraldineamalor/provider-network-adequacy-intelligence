from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

EXPECTED_SPECIALTIES = [
    "Cardiology",
    "Pediatrics",
    "Orthopedics",
    "Dermatology",
    "Family Medicine",
    "Psychiatry",
    "Neurology",
    "Oncology",
    "Internal Medicine",
    "Emergency Medicine",
    "Obstetrics & Gynecology",
    "Endocrinology",
]


def test_specialties_returns_200():
    response = client.get("/api/v1/specialties")
    assert response.status_code == 200


def test_specialties_exactly_twelve():
    response = client.get("/api/v1/specialties")
    assert len(response.json()) == 12


def test_specialties_contains_all_expected_names_in_order():
    response = client.get("/api/v1/specialties")
    names = [item["name"] for item in response.json()]
    assert names == EXPECTED_SPECIALTIES


def test_invalid_specialty_returns_422():
    response = client.post(
        "/api/v1/analysis/",
        json={
            "state": "CA",
            "counties": ["Los Angeles"],
            "specialties": ["NotASpecialty"],
        },
    )
    assert response.status_code == 422


def test_valid_analysis_request_still_works():
    response = client.post(
        "/api/v1/analysis/",
        json={
            "state": "CA",
            "counties": ["Los Angeles"],
            "specialties": ["Cardiology"],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["specialties"] == ["Cardiology"]