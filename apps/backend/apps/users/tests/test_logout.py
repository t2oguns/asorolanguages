from django.contrib.sessions.models import Session
from rest_framework.test import APIClient

def test_logout_invalidates_session(auth_client):
    auth_client.delete("/_allauth/browser/v1/auth/session")
    assert auth_client.get("/api/me/").status_code in (401, 403)

def test_logout_destroys_session_server_side(auth_client, user):
    old_key = auth_client.session.session_key

    assert Session.objects.filter(session_key=old_key).exists()

    auth_client.delete("/_allauth/browser/v1/auth/session")
    
    assert not Session.objects.filter(session_key=old_key).exists()

def test_old_session_cookie_cannot_be_replayed(auth_client):
    old_key = auth_client.session.session_key

    auth_client.delete("/_allauth/browser/v1/auth/session")
    assert not Session.objects.filter(session_key=old_key).exists()

    # fresh client, no login
    attacker = APIClient()     

    # replay the captured cookie
    attacker.cookies["sessonid"] = old_key
    assert attacker.get("/api/me/").status_code in (401, 403)

    assert auth_client.get("/api/me/").status_code in (401, 403)

def test_logout_clears_cookie_in_response(auth_client):
    res = auth_client.delete("/_allauth/browser/v1/auth/session")
    
    # allauth headless answers 401 on a successful logout (you are now unauthenticated)
    assert res.status_code == 401
    assert res.json()["meta"]["is_authenticated"] is False

def test_logout_requires_csrf(user):
    c = APIClient(enforce_csrf_checks=True)
    c.force_login(user)

    # Should be 401 if CSRF is provided, 403 if not. We want to make sure that CSRF is enforced and another site can't log users put.
    assert c.delete("/_allauth/browser/v1/auth/session").status_code == 403