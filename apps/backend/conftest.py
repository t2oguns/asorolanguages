from urllib.parse import parse_qs, urlparse
import pytest
from rest_framework.test import APIClient
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from apps.users.models import User
from tests.factories import (
    make_lesson,
    make_module,
    make_unit,
    make_user,
    make_user_progress,
    make_lesson_progress
)
from apps.courses.models import PUBLISH_STATUS


@pytest.fixture(autouse=True)
def _settings(settings):
    # Make tests independent of your .env
    settings.CORS_ALLOWED_ORIGINS = ["http://localhost:3000"]
    settings.CSRF_TRUSTED_ORIGINS = ["http://localhost:3000"]
    settings.SESSION_COOKIE_SECURE = settings.CSRF_COOKIE_SECURE = False
    settings.SESSION_COOKIE_DOMAIN = settings.CSRF_COOKIE_DOMAIN = None


@pytest.fixture
def user(db):
    return make_user()


@pytest.fixture
def auth_client(user):
    c = APIClient()
    c.force_login(user)
    return c


@pytest.fixture
def google_login(db, client, mocker):
    """Run the real allauth flow end to end, faking only Google's network calls."""
    def _login(email="ada@example.com", verified=True, uid="g-123",
               name="Ada Lovelace", picture="https://img.example/ada.png"):
        callback_url = "http://localhost:3000/auth/callback"

        # 1. Start the flow exactly as the frontend form does (stores `state` in the session)
        start = client.post("/_allauth/browser/v1/auth/provider/redirect", {
            "provider": "google", "process": "login", "callback_url": callback_url,
        })
        assert start.status_code == 302
        state = parse_qs(urlparse(start["Location"]).query)["state"][0]

        # 2. Fake the two server-to-server calls to Google
        profile = {"sub": uid, "email": email, "email_verified": verified,
                   "name": name, "picture": picture}
        mocker.patch(
            "allauth.socialaccount.providers.oauth2.client.OAuth2Client.get_access_token",
            return_value={"access_token": "fake"},
        )
        def fake_complete_login(self, request, app, token, **kwargs):
            return self.get_provider().sociallogin_from_response(request, profile)
        mocker.patch.object(GoogleOAuth2Adapter, "complete_login", fake_complete_login)

        # 3. Google redirects the browser back to Django's callback
        return client.get("/accounts/google/login/callback/", {"code": "fake", "state": state})
    return _login

@pytest.fixture
def unit(db):
    return make_unit()

@pytest.fixture
def module(unit):
    return make_module(unit=unit)

@pytest.fixture
def lesson(module):
    return make_lesson(module=module, publication_status=PUBLISH_STATUS.PUBLISHED)

@pytest.fixture
def lesson_draft(module):
    return make_lesson(module=module)


@pytest.fixture
def user_progress(user):
    return make_user_progress(user=user)


@pytest.fixture
def lesson_progress(user_progress, lesson):
    return make_lesson_progress(lesson=lesson, user_progress=user_progress)
