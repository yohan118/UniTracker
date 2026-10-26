from app import app

client = app.test_client()


# only /health is tested: there is no database in GitHub Actions
def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
