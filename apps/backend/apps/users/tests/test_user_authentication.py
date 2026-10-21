from apps.users.models import UserProfile

def test_me_requires_auth(client, db):
    # DRF session auth gives 403 for unauthenticated users, but DRF token auth gives 401. Either is fine.
    assert client.get("/api/me/").status_code in (401, 403)  
 
def test_me_returns_profile(auth_client, user):
    p = UserProfile.objects.create(user=user, display_name="Ex", avatar_url="https://i/x.png")
    r = auth_client.get("/api/me/")
    assert r.status_code == 200
    assert r.json() == {"id": user.id, "email": user.email, "is_superuser": user.is_superuser,
                        "profile": {"user": user.id, "display_name": "Ex", "avatar_url": "https://i/x.png"}}

def test_me_survives_missing_profile(auth_client):
    assert auth_client.get("/api/me/").status_code == 200