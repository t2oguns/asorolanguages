from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from apps.exercises.lessons import lesson_payload, deliver_lesson, submit_lesson
from apps.exercises.models import ExerciseAcceptedAnswer, ExerciseAttempt, LessonAttempt, LessonExercise
from apps.exercises.services import publish_exercise, unpublish_exercise
from apps.progress.models import LexemeProgress, LexemeReviewLog, UserLessonProgress

pytestmark = pytest.mark.django_db


@pytest.fixture
def batch_lesson(lesson, exercise_factory):
    for position in range(2):
        exercise = exercise_factory()
        ExerciseAcceptedAnswer.objects.create(exercise=exercise, text="hello")
        publish_exercise(exercise.pk)
        LessonExercise.objects.create(lesson=lesson, exercise=exercise, position=position)
    return lesson


def responses(session, *values):
    return [{"exercise_id": attempt["id"], "response": value} for attempt, value in zip(session.exercises, values)]


def test_each_start_is_fresh_and_does_not_persist_partial_progress(user, batch_lesson):
    session = deliver_lesson(user=user, lesson=batch_lesson)
    assert deliver_lesson(user=user, lesson=batch_lesson).pk != session.pk
    assert LessonAttempt.objects.count() == 2
    assert not UserLessonProgress.objects.exists()
    payload = lesson_payload(session)
    assert len(payload["exercises"]) == 2
    assert payload["exercises"][0]["accepted_answers"][0]["text"] == "hello"
    assert not ExerciseAttempt.objects.exists()
    assert payload["exercises"][0]["ignore_diacritics"] is False
    assert not LexemeProgress.objects.exists()


def test_first_responses_are_scored_and_practice_does_not_advance_fsrs(user, batch_lesson):
    session = deliver_lesson(user=user, lesson=batch_lesson)
    data = responses(session, "wrong", "hello")
    sense = str(session.exercises[0]["targets"][0]["sense_id"])
    data.append({"exercise_id": data[0]["exercise_id"], "response": "hello", "recall_ratings": {sense: 4}})
    result = submit_lesson(user=user, session_id=session.pk, responses=data)
    assert result.server_result["first_try_correct"] == 1
    assert LexemeReviewLog.objects.get().rating == 1
    assert LexemeProgress.objects.get().reps == 1
    assert LexemeReviewLog.objects.count() == 1
    assert ExerciseAttempt.objects.count() == 3
    assert session.answers.order_by("sequence").first().response == "wrong"
    assert not result.server_result["results"][1]["target_results"][0]["fsrs_eligible"]
    progress = UserLessonProgress.objects.get()
    assert progress.status == UserLessonProgress.Status.COMPLETED and progress.best_score == 50


def test_retries_do_not_duplicate_records_or_change_ratings(user, batch_lesson):
    session = deliver_lesson(user=user, lesson=batch_lesson)
    data = responses(session, "hello", "hello")
    sense = str(session.exercises[0]["targets"][0]["sense_id"])
    data[0]["recall_ratings"] = {sense: 2}
    first = submit_lesson(user=user, session_id=session.pk, responses=data)
    retry = submit_lesson(user=user, session_id=session.pk, responses=data)
    assert first.server_result == retry.server_result
    assert LexemeProgress.objects.get().reps == 1
    assert ExerciseAttempt.objects.count() == 2
    data[0]["recall_ratings"][sense] = 4
    with pytest.raises(ValidationError, match="already submitted"):
        submit_lesson(user=user, session_id=session.pk, responses=data)


@pytest.mark.parametrize("invalid", ["missing", "reordered", "foreign", "twice_requeued", "bad_rating"])
def test_invalid_batch_has_no_partial_progress(user, batch_lesson, invalid):
    session = deliver_lesson(user=user, lesson=batch_lesson)
    data = responses(session, "wrong", "hello")
    if invalid == "missing": data.pop()
    elif invalid == "reordered": data.reverse()
    elif invalid == "foreign": data[0]["exercise_id"] = str(uuid4())
    elif invalid == "twice_requeued": data.extend([data[0], data[0]])
    else: data[0]["recall_ratings"] = []
    with pytest.raises(ValidationError):
        submit_lesson(user=user, session_id=session.pk, responses=data)
    assert not LexemeProgress.objects.exists()
    assert not ExerciseAttempt.objects.exists()
    assert not UserLessonProgress.objects.filter(status=UserLessonProgress.Status.COMPLETED).exists()


def test_delivered_exercises_survive_unpublication(user, batch_lesson):
    session = deliver_lesson(user=user, lesson=batch_lesson)
    unpublish_exercise(session.exercises[0]['id'])
    assert submit_lesson(user=user, session_id=session.pk, responses=responses(session, 'hello', 'hello')).submitted_at


def test_batch_failure_rolls_back_every_exercise(user, batch_lesson, mocker):
    session = deliver_lesson(user=user, lesson=batch_lesson)
    mocker.patch.object(ExerciseAttempt.objects, "create", side_effect=RuntimeError("unavailable"))
    with pytest.raises(RuntimeError):
        submit_lesson(user=user, session_id=session.pk, responses=responses(session, "hello", "hello"))
    assert not LexemeProgress.objects.exists()
    assert not LexemeReviewLog.objects.exists()
    assert not ExerciseAttempt.objects.filter(submitted_at__isnull=False).exists()




def test_delivery_reads_do_not_grow_per_exercise(user, batch_lesson, exercise_factory):
    with CaptureQueriesContext(connection) as first:
        deliver_lesson(user=user, lesson=batch_lesson)
    for position in (2, 3):
        exercise = exercise_factory()
        ExerciseAcceptedAnswer.objects.create(exercise=exercise, text="hello")
        publish_exercise(exercise.pk)
        LessonExercise.objects.create(lesson=batch_lesson, exercise=exercise, position=position)
    with CaptureQueriesContext(connection) as second:
        deliver_lesson(user=user, lesson=batch_lesson)
    assert len(second) == len(first)  # One delivery row regardless of exercise count.


def test_api_delivers_answers_and_accepts_one_batch(auth_client, user, batch_lesson):
    result = auth_client.post(reverse("apps.courses:start-lesson-session", kwargs={"code": batch_lesson.code}), {"session_id": str(uuid4())}, format="json")
    assert result.status_code == 201
    assert result["Cache-Control"] == "private, no-store"
    session = LessonAttempt.objects.get(pk=result.json()["lesson_attempt_id"])
    url = reverse("apps.courses:submit-lesson-session", kwargs={"code": batch_lesson.code, "session_id": session.pk})
    submitted = auth_client.post(url, {"responses": responses(session, "hello", "hello"), "score": 999}, format="json")
    assert submitted.status_code == 200
    assert submitted.json() == {"lesson_attempt_id": str(session.pk), "submitted": True}
    assert LexemeProgress.objects.get().reps == 1


def test_sessions_are_private_and_empty_submit_cannot_complete(auth_client, user, batch_lesson, django_user_model, client):
    other = django_user_model.objects.create_user(email="other-session@example.com")
    session = deliver_lesson(user=other, lesson=batch_lesson)
    kwargs = {"code": batch_lesson.code, "session_id": session.pk}
    url = f"/api/v1/courses/lesson/{batch_lesson.code}/sessions/{session.pk}/"
    assert auth_client.get(url).status_code == 404
    assert client.get(url).status_code == 404
    submit_url = reverse("apps.courses:submit-lesson-session", kwargs=kwargs)
    assert auth_client.post(submit_url, {"responses": responses(session, "hello", "hello")}, format="json").status_code == 404
    removed_url = f"/api/v1/courses/lesson/{batch_lesson.code}/submit/"
    assert auth_client.post(removed_url, {}, format="json").status_code == 404
    assert not UserLessonProgress.objects.filter(status=UserLessonProgress.Status.COMPLETED).exists()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("distinct_sessions", [False, True])
def test_concurrent_batches_preserve_reviews(user, batch_lesson, distinct_sessions):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from django.contrib.auth import get_user_model
    from django.db import close_old_connections, connections

    if connection.vendor != "postgresql":
        pytest.skip("Row-lock concurrency requires PostgreSQL.")
    first = deliver_lesson(user=user, lesson=batch_lesson)
    second = deliver_lesson(user=user, lesson=batch_lesson) if distinct_sessions else first
    barrier = Barrier(2)
    batches = [(session.pk, responses(session, "hello", "hello")) for session in (first, second)]

    def submit(session_id, data):
        close_old_connections()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET lock_timeout = '5s'")
            learner = get_user_model().objects.get(pk=user.pk)
            barrier.wait(timeout=10)
            return submit_lesson(user=learner, session_id=session_id, responses=data).server_result
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(submit, session_id, data) for session_id, data in batches]
        results = [future.result(timeout=20) for future in futures]
    count = 2 if distinct_sessions else 1
    assert LexemeProgress.objects.get(user_progress__user=user).reps == count
    assert LexemeReviewLog.objects.count() == count
    assert ExerciseAttempt.objects.count() == count * 2
    if not distinct_sessions:
        assert results[0] == results[1]


def test_disagreements_are_saved_silently_and_do_not_drive_progress(auth_client, user, batch_lesson):
    session = deliver_lesson(user=user, lesson=batch_lesson)
    data = responses(session, 'wrong', 'hello')
    sense = str(session.exercises[0]['targets'][0]['sense_id'])
    data[0]['recall_ratings'] = {sense: 4}
    # A client grading the second response wrong is allowed to queue practice,
    # even though the server finds it correct.
    data.append({'exercise_id': data[1]['exercise_id'], 'response': 'hello'})
    url = reverse('apps.courses:submit-lesson-session', kwargs={'code': batch_lesson.code, 'session_id': session.pk})
    result = auth_client.post(url, {'responses': data}, format='json')
    assert result.status_code == 200
    assert result.json() == {'lesson_attempt_id': str(session.pk), 'submitted': True}
    session.refresh_from_db()
    assert session.server_result['mean_score'] == .5
    assert LexemeReviewLog.objects.get().rating == 1
    assert UserLessonProgress.objects.get().best_score == 50
    # Client observations remain private audit data; no resume endpoint exposes them.
    assert session.submission[0]['recall_ratings'] == {sense: 4}
    assert 'responses' not in lesson_payload(session)
    assert 'server_result' not in lesson_payload(session)


def test_delivery_rejects_a_concurrent_content_change(user, batch_lesson, mocker):
    from apps.exercises.serializers import ExerciseSerializer
    original = ExerciseSerializer.to_representation

    def change_content(serializer, exercise):
        data = original(serializer, exercise)
        unpublish_exercise(exercise.pk)
        return data

    mocker.patch.object(ExerciseSerializer, 'to_representation', change_content)
    with pytest.raises(ValidationError, match='during delivery'):
        deliver_lesson(user=user, lesson=batch_lesson)
    assert not LessonAttempt.objects.exists()


def test_start_request_cannot_resume_an_old_session(auth_client, user, batch_lesson):
    old = deliver_lesson(user=user, lesson=batch_lesson)
    url = reverse('apps.courses:start-lesson-session', kwargs={'code': batch_lesson.code})
    result = auth_client.post(url, {'session_id': str(old.pk)}, format='json')
    assert result.status_code == 201
    assert result.json()['lesson_attempt_id'] != str(old.pk)
    assert 'responses' not in result.json()
    assert not UserLessonProgress.objects.exists()


def test_a_new_visit_preserves_completed_progress_without_scheduling_again(user, batch_lesson):
    first = deliver_lesson(user=user, lesson=batch_lesson)
    submit_lesson(user=user, session_id=first.pk, responses=responses(first, 'hello', 'hello'))
    progress = UserLessonProgress.objects.get()
    completed_at = progress.completed_at
    second = deliver_lesson(user=user, lesson=batch_lesson)
    assert second.pk != first.pk
    assert not second.answers.exists()
    progress.refresh_from_db()
    assert progress.status == UserLessonProgress.Status.COMPLETED
    assert progress.best_score == 100 and progress.completed_at == completed_at
    assert LexemeProgress.objects.get().reps == 1
