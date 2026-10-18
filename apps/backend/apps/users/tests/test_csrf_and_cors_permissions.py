from rest_framework.test import APIClient

def test_mutation_without_csrf_token_is_rejected(user):
    """Test that CSRF protection is enabled for authenticated users."""
    c = APIClient(enforce_csrf_checks=True)
    c.force_login(user)
    assert c.post("/api/lesson-complete/{random_lesson}", {"name": "x"}, format="json").status_code == 403

def test_cors_allows_frontend_origin(client, db):
    """ Test that CORS is configured to allow the frontend origin."""
    # Sends get request to session endpoint with CORS headers, expects 200 and correct CORS headers in response
    r = client.options("/_allauth/browser/v1/config",
                       HTTP_ORIGIN="http://localhost:3000",
                       HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET")
    assert r["Access-Control-Allow-Origin"] == "http://localhost:3000"
    assert r["Access-Control-Allow-Credentials"] == "true"

def test_cors_rejects_unknown_origin(client, db):
    r = client.options("/_allauth/browser/v1/config",
                       HTTP_ORIGIN="https://evil.example",
                       HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET")
    assert "Access-Control-Allow-Origin" not in r
