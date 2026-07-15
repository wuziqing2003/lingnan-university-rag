from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)






def  test_health_status_code():
    response = client.get("/health")
    assert response.status_code == 200

def test_health_body():
    response = client.get("/health")
    assert response.json()["status"] == "ok"

def  test_create_user_invalid_payload_returns_422():
    response = client.post(
        "/user",
        json = {"username":"ab","password":"12345"}
        
        )
    assert response.status_code == 422
