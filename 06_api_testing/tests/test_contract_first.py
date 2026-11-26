from fastapi.testclient import TestClient
from app.main import app


def test_versioned_documentation():
    """OpenAPI доступна отдельно для v1 и v2."""
    with TestClient(app) as client:
        for version in ("v1", "v2"):
            response = client.get(f"/api/{version}/openapi.json")
            assert response.status_code == 200
            assert "/olympiads" in response.json()["paths"]


def test_guest_cannot_create_olympiad():
    """Гость не может создать карточку олимпиады."""
    with TestClient(app) as client:
        response = client.post("/api/v1/olympiads", json={})
        assert response.status_code == 401
