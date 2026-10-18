from allauth.socialaccount.models import SocialAccount
from apps.users.models import User

def test_new_google_user_is_created_with_profile(google_login):
    resp = google_login(email="ada@example.com", name="Ada Lovelace")

    assert resp.status_code == 302
    # Change to frontend URL in production
    assert resp["Location"].startswith("http://localhost:3000/auth/callback")
    u = User.objects.get(email="ada@example.com")
    assert u.profile.display_name == "Ada Lovelace"
    assert u.profile.avatar_url == "https://img.example/ada.png"
    assert not u.has_usable_password()
    assert SocialAccount.objects.filter(user=u, provider="google", uid="g-123").exists()

def test_login_creates_session(google_login, client):
    google_login()
    assert "_auth_user_id" in client.session

def test_long_name_is_truncated(google_login):
    google_login(email="long@example.com", name="x" * 300)
    assert len(User.objects.get(email="long@example.com").profile.display_name) == 100

def test_returning_user_does_not_duplicate(google_login, client):
    google_login()
    client.logout()
    google_login()
    assert User.objects.filter(email="ada@example.com").count() == 1
    assert SocialAccount.objects.count() == 1

def test_verified_email_links_to_existing_user(google_login, user):
    google_login(email=user.email, verified=True)
    assert User.objects.count() == 1
    assert user.socialaccount_set.filter(provider="google").exists()

def test_unverified_email_never_links_to_existing_user(google_login, client, user):
    google_login(email=user.email, verified=False)
    assert not user.socialaccount_set.exists()
    assert "_auth_user_id" not in client.session

def test_password_signup_is_closed(client, db):
    r = client.post("/_allauth/browser/v1/auth/signup",
                    {"email": "x@example.com", "password": "Sup3rSecret!"},
                    content_type="application/json")
    assert r.status_code >= 400
    assert not User.objects.filter(email="x@example.com").exists()

def test_password_login_impossible_for_social_users(client, user):
    r = client.post("/_allauth/browser/v1/auth/login",
                    {"email": user.email, "password": ""},
                    content_type="application/json")
    assert r.status_code >= 400
