import pytest
from apps.courses.models import Unit, Module, Lesson, PUBLISH_STATUS
from apps.progress import services
from apps.progress.models import UserProgress, UserLessonProgress
from datetime import datetime, timezone as dt_timezone
from django.utils import timezone
from unittest.mock import call, patch


@pytest.fixture
def completed_at():
    return datetime(2026, 1, 10, 12, 0, tzinfo=dt_timezone.utc)


def test_creates_user_progress_when_missing(user, lesson):
    assert not UserProgress.objects.filter(user=user).exists()

    # Patch scoring to standardize
    with patch(
        "apps.progress.services.handle_scoring", return_value=85
    ) as scoring:
        result = services.complete_lesson(user=user, lesson=lesson)

    user_progress = UserProgress.objects.get(user=user)

    assert UserProgress.objects.filter(user=user).count() == 1
    assert result.user_progress == user_progress
    # scoring.assert_called_once_with(lesson)

def test_creates_completed_lesson_progress(user, lesson):
    with patch("apps.progress.services.handle_scoring", return_value=85):
        result = services.complete_lesson(user, lesson)

    result.refresh_from_db()

    assert result.status == UserLessonProgress.Status.COMPLETED
    assert result.best_score == 85
    assert result.completed_at is not None
    assert timezone.is_aware(result.completed_at)
    assert result.lesson == lesson

def test_sets_completion_timestamp_on_creation(user, lesson, completed_at):
    with (
        patch("apps.progress.services.handle_scoring", return_value=90),
        patch("django.utils.timezone.now", return_value=completed_at),
    ):
        result = services.complete_lesson(user, lesson)

    assert result.completed_at == completed_at

def test_completion_date_does_not_change(user, lesson):
    lesson_completion_1 = services.complete_lesson(user=user, lesson=lesson)
    lesson_completion_2 = services.complete_lesson(user=user, lesson=lesson)

    assert lesson_completion_1.completed_at == lesson_completion_2.completed_at


