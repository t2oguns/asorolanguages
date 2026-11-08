from datetime import datetime, timedelta, timezone as utc_timezone

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from fsrs import Card, Rating, Scheduler, State

from apps.exercises.models import ExerciseAttempt, LessonAttempt, LessonExercise
from apps.exercises.lessons import deliver_lesson, submit_lesson
from apps.progress.models import LexemeProgress, LexemeReviewLog, UserProgress
from apps.progress.scheduling import due_lexeme_progress
from apps.vocabulary.models import LexemeSense

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def deterministic_scheduler(settings):
    settings.FSRS_ENABLE_FUZZING = False


@pytest.fixture
def review_lesson(published_exercise, lesson):
    LessonExercise.objects.create(lesson=lesson, exercise=published_exercise, position=0)
    return lesson


def submit_review(*, user, session_id, response, recall_ratings=None):
    session = LessonAttempt.objects.get(pk=session_id)
    submit_lesson(user=user, session_id=session_id, responses=[{
        'exercise_id': session.exercises[0]['id'], 'response': response,
        'recall_ratings': recall_ratings,
    }])
    return session.answers.get()


@pytest.fixture
def review(review_lesson, user):
    def submit(response="hello", ratings=None):
        attempt = deliver_lesson(user=user, lesson=review_lesson)
        return submit_review(user=user, session_id=attempt.pk, response=response, recall_ratings=ratings)
    return submit


def test_first_review_initializes_memory_and_records_replay_data(review, vocabulary_sense, user):
    result = review()
    progress = LexemeProgress.objects.get(user_progress__user=user, lexeme_sense=vocabulary_sense)
    log = progress.reviews.get()
    assert progress.reps == 1 and progress.lapses == 0
    assert progress.state == State.Learning
    assert progress.step == 1
    assert progress.stability > 0
    assert 1 <= progress.difficulty <= 10
    assert progress.due == progress.last_review + timedelta(minutes=10)
    assert log.rating == Rating.Good
    assert log.attempt_id == result.pk
    assert log.reviewed_at == result.submitted_at == progress.last_review
    assert log.package_version == "6.3.2"
    assert log.policy_version == "exercise-v1"
    assert log.card_before["stability"] is None
    assert log.card_before["last_review"] is None
    assert log.card_before["card_id"] == progress.pk
    engine = Scheduler.from_dict(log.scheduler_config)
    replay, _ = engine.review_card(Card.from_dict(log.card_before), Rating(log.rating), review_datetime=log.reviewed_at)
    assert replay.to_dict() == log.card_after
    assert result.target_results[0]["due"] == progress.due.isoformat()


def test_failure_during_learning_is_not_a_lapse(review, user):
    review("wrong")
    progress = LexemeProgress.objects.get(user_progress__user=user)
    assert progress.state == State.Learning
    assert progress.lapses == 0
    assert progress.reviews.get().rating == Rating.Again
    assert progress.due == progress.last_review + timedelta(minutes=1)


def test_lapse_moves_a_review_card_into_relearning(review, vocabulary_sense, user, mocker):
    now = datetime(2027, 1, 1, tzinfo=utc_timezone.utc)
    clock = mocker.patch("django.utils.timezone.now", return_value=now)
    review(ratings={str(vocabulary_sense.pk): 4})
    progress = LexemeProgress.objects.get(user_progress__user=user)
    assert progress.state == State.Review and progress.step is None
    clock.return_value = progress.due
    review("wrong")
    progress.refresh_from_db()
    assert progress.reps == 2 and progress.lapses == 1
    assert progress.state == State.Relearning and progress.step == 0
    assert progress.due == progress.last_review + timedelta(minutes=10)
    assert progress.reviews.count() == 2


@pytest.mark.parametrize("rating", [1, 2, 3, 4])
def test_correct_answer_accepts_learner_recall_rating(review, vocabulary_sense, rating):
    result = review(ratings={str(vocabulary_sense.pk): rating})
    assert result.target_results[0]["rating"] == rating
    assert LexemeReviewLog.objects.get().rating == rating


@pytest.mark.parametrize("ratings", [{"unknown": 3}, {"1": 0}, {"1": True}, [], "good"])
def test_invalid_ratings_do_not_write_progress(review_lesson, user, ratings):
    attempt = deliver_lesson(user=user, lesson=review_lesson)
    with pytest.raises(ValidationError):
        submit_review(user=user, session_id=attempt.pk, response="hello", recall_ratings=ratings)
    assert not LexemeProgress.objects.exists()
    assert not LexemeReviewLog.objects.exists()
    attempt.refresh_from_db()
    assert attempt.submitted_at is None


@pytest.mark.parametrize("rating", [2, 3, 4])
def test_incorrect_answer_silently_downgrades_rating(review, vocabulary_sense, rating):
    answer = review("wrong", ratings={str(vocabulary_sense.pk): rating})
    assert answer.target_results[0]['rating'] == 1
    assert LexemeReviewLog.objects.get().rating == 1


def test_retry_cannot_change_a_recorded_rating(review_lesson, user, vocabulary_sense):
    attempt = deliver_lesson(user=user, lesson=review_lesson)
    submit_review(user=user, session_id=attempt.pk, response="hello", recall_ratings={str(vocabulary_sense.pk): 2})
    submit_review(user=user, session_id=attempt.pk, response="hello", recall_ratings={str(vocabulary_sense.pk): 2})
    with pytest.raises(ValidationError, match="already submitted"):
        submit_review(user=user, session_id=attempt.pk, response="hello", recall_ratings={str(vocabulary_sense.pk): 4})
    assert LexemeProgress.objects.get().reps == 1
    assert LexemeReviewLog.objects.count() == 1


def test_scheduler_configuration_is_recorded(review, settings):
    settings.FSRS_DESIRED_RETENTION = 0.85
    review()
    log = LexemeReviewLog.objects.get()
    assert log.scheduler_config["desired_retention"] == 0.85
    assert not log.scheduler_config["enable_fuzzing"]
    assert len(log.scheduler_config["parameters"]) == 21


def test_review_log_failure_rolls_back_attempt_and_card(review, mocker):
    mocker.patch.object(LexemeReviewLog.objects, "create", side_effect=RuntimeError("unavailable"))
    with pytest.raises(RuntimeError):
        review()
    assert not LexemeProgress.objects.exists()
    assert not LexemeReviewLog.objects.exists()
    assert not ExerciseAttempt.objects.exists()


def test_due_queue_is_ordered_and_scoped_to_the_learner_and_language(user, django_user_model, vocabulary_sense, learning_language):
    owner = UserProgress.objects.create(user=user)
    now = datetime(2027, 1, 1, tzinfo=utc_timezone.utc)
    first = LexemeProgress.objects.create(user_progress=owner, lexeme_sense=vocabulary_sense, due=now - timedelta(days=1))
    second_sense = LexemeSense.objects.create(lexeme=vocabulary_sense.lexeme, meaning="another meaning")
    second = LexemeProgress.objects.create(user_progress=owner, lexeme_sense=second_sense, due=now)
    third_sense = LexemeSense.objects.create(lexeme=vocabulary_sense.lexeme, meaning="third meaning")
    LexemeProgress.objects.create(user_progress=owner, lexeme_sense=third_sense, due=now + timedelta(days=1))
    other = django_user_model.objects.create_user(email="other@example.com")
    LexemeProgress.objects.create(user_progress=UserProgress.objects.create(user=other), lexeme_sense=vocabulary_sense, due=now)
    assert list(due_lexeme_progress(user=user, at=now)) == [first, second]
    assert list(due_lexeme_progress(user=user, at=now, limit=1)) == [first]
    assert list(due_lexeme_progress(user=user, at=now, language_id=learning_language.pk)) == [first, second]
    assert not due_lexeme_progress(user=user, at=now, language_id=999).exists()
    with pytest.raises(ValidationError):
        due_lexeme_progress(user=user, limit=True)
    with pytest.raises(IntegrityError), transaction.atomic():
        LexemeProgress.objects.create(user_progress=owner, lexeme_sense=vocabulary_sense)

