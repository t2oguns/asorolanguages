from apps.users.models import UserProfile, User

def test_user_cannot_see_other_users_progress(auth_client, user, db):
    """other = User.objects.create_user(email="other@example.com")
    Project.objects.create(owner=other, name="secret")
    Project.objects.create(owner=user, name="mine")
    names = [p["name"] for p in auth_client.get("/api/projects/").json()]
    assert names == ["mine"]"""
    pass  # TODO: implement for User Progress model and API

def test_user_cannot_complete_other_users_lesson(auth_client, db):
    """
    other = User.objects.create_user(email="other@example.com")
    p = Project.objects.create(owner=other, name="secret")
    assert auth_client.patch(f"/api/projects/{p.id}/", {"name": "x"}, format="json").status_code == 404
    """
    pass  # TODO: implement  model and API


