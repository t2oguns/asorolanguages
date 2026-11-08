"""Lesson progress is written only by authoritative answer submission."""
from datetime import datetime, timezone as utc_timezone

import pytest
from django.utils import timezone

from apps.exercises.lessons import deliver_lesson, submit_lesson
from apps.exercises.models import LessonExercise
from apps.progress.models import UserLessonProgress, UserProgress

pytestmark = pytest.mark.django_db


@pytest.fixture
def submit_answers(user, lesson, published_exercise):
    LessonExercise.objects.create(lesson=lesson, exercise=published_exercise, position=0)

    def submit(correct=True):
        session = deliver_lesson(user=user, lesson=lesson)
        submit_lesson(user=user, session_id=session.pk, responses=[{
            'exercise_id': str(published_exercise.pk), 'response': 'hello' if correct else 'wrong',
        }])
        return UserLessonProgress.objects.get(user_progress__user=user, lesson=lesson)

    return submit


def test_submission_creates_user_progress_when_missing(user, submit_answers):
    assert not UserProgress.objects.filter(user=user).exists()
    result = submit_answers()
    assert UserProgress.objects.filter(user=user).count() == 1
    assert result.user_progress == UserProgress.objects.get(user=user)


def test_submission_records_a_graded_score_and_completion(lesson, submit_answers):
    result = submit_answers()
    assert result.status == UserLessonProgress.Status.COMPLETED
    assert result.best_score == 100
    assert result.completed_at is not None and timezone.is_aware(result.completed_at)
    assert result.lesson == lesson


def test_submission_sets_completion_timestamp(submit_answers, mocker):
    now = datetime(2026, 1, 10, 12, tzinfo=utc_timezone.utc)
    mocker.patch('django.utils.timezone.now', return_value=now)
    assert submit_answers().completed_at == now


def test_later_submissions_preserve_first_completion_date(submit_answers):
    first = submit_answers()
    second = submit_answers()
    assert first.completed_at == second.completed_at


@pytest.mark.parametrize('previous,correct,expected', [(70, True, 100), (90, False, 90), (0, True, 100)])
def test_submission_preserves_the_best_authoritative_score(lesson_progress, submit_answers, previous, correct, expected):
    lesson_progress.status = UserLessonProgress.Status.COMPLETED
    lesson_progress.best_score = previous
    lesson_progress.completed_at = timezone.now()
    lesson_progress.save()
    assert submit_answers(correct).best_score == expected


def test_completed_progress_is_exposed_by_the_lesson_api(auth_client, lesson, submit_answers):
    from django.urls import reverse

    submitted = submit_answers()
    response = auth_client.get(reverse('apps.courses:get-lesson', kwargs={'code': lesson.code}))
    assert response.status_code == 200
    progress = response.json()['progress']
    assert progress['status'] == UserLessonProgress.Status.COMPLETED
    assert progress['best_score'] == submitted.best_score
    assert progress['completed_at'] is not None
