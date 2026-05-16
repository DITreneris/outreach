from fastapi.testclient import TestClient

from cpb_outreach.api.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "cpb-school-outreach"
