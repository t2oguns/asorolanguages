from apps.users.models import User
import pytest

def test_create_user_without_password_is_unusable(db):
    u = User.objects.create_user(email="a@Example.com")
    assert not u.has_usable_password()

def test_email_required(db):
    with pytest.raises(ValueError):
        User.objects.create_user(email="")

def test_superuser_can_use_password(db):
    u = User.objects.create_superuser(email="root@example.com", password="pw12345!")
    assert u.is_staff and u.is_superuser and u.check_password("pw12345!")