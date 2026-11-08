"""Deliver Exercise data once; grade a complete lesson submission atomically."""
from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID, uuid4

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone

from apps.courses.models import PUBLISH_STATUS
from apps.exercises.grading import grade_exercise
from apps.exercises.models import Exercise, ExerciseAttempt, ExerciseTarget, LessonAttempt, PromptBlock
from apps.exercises.serializers import ExerciseSerializer
from apps.progress.models import UserLessonProgress, UserProgress
from apps.progress.scheduling import parse_recall_ratings, schedule_answer_reviews


@transaction.atomic
def deliver_lesson(*, user, lesson):
    """Each visit creates a fresh delivery; no partial learner progress is saved."""
    get_user_model().objects.select_for_update().get(pk=user.pk)
    if lesson.publication_status != PUBLISH_STATUS.PUBLISHED:
        raise ValidationError("This lesson is not published.")
    exercises = list(Exercise.objects.filter(lesson_placements__lesson=lesson, is_published=True)
        .select_related('language', 'explanation_media').prefetch_related(
            Prefetch('targets', queryset=ExerciseTarget.objects.select_related('sense__lexeme')),
            Prefetch('prompt_blocks', queryset=PromptBlock.objects.select_related('media', 'expression', 'lexeme_sense__lexeme')),
            'options__media', 'accepted_answers', 'fill_blank_slots__accepted_answers',
            'matching_pairs__left_media', 'matching_pairs__right_media',
        ).order_by('lesson_placements__position'))
    if not exercises:
        raise ValidationError("This lesson has no published exercises.")
    payload = deepcopy(ExerciseSerializer(exercises, many=True).data)
    publications = dict(Exercise.objects.filter(pk__in=[row.pk for row in exercises], is_published=True).values_list('pk', 'published_at'))
    if any(publications.get(row.pk) != row.published_at for row in exercises):
        raise ValidationError("Lesson content changed during delivery. Try again.")
    session = LessonAttempt.objects.create(
        id=uuid4(), user=user, lesson=lesson, exercises=payload,
        lesson_snapshot={'id': lesson.pk, 'code': lesson.code, 'title': lesson.title, 'description': lesson.description},
    )
    return session


def lesson_payload(session):
    return {
        **submission_receipt(session), 'learner_id': str(session.user_id),
        'lesson': session.lesson_snapshot, 'exercises': session.exercises,
    }


def submission_receipt(session):
    return {'lesson_attempt_id': str(session.pk), 'submitted': session.submitted_at is not None}


def _canonical_responses(responses):
    if not isinstance(responses, list) or not responses or len(responses) > 100:
        raise ValidationError("Submit an ordered list of lesson answers (at most 100).")
    
    canonical = []
    
    for item in responses:
        if not isinstance(item, dict) or 'exercise_id' not in item or 'response' not in item:
            raise ValidationError("Each answer needs an exercise_id and raw response.")
        
        try:
            exercise_id = str(UUID(str(item['exercise_id'])))
        except (ValueError, TypeError, AttributeError):
            raise ValidationError("Invalid exercise ID.")
        
        entry = {'exercise_id': exercise_id, 'response': deepcopy(item['response']),
                 'recall_ratings': deepcopy(item.get('recall_ratings') or {})}
        
        # An empty non-dictionary rating is still malformed.
        if item.get('recall_ratings') is not None and not isinstance(item['recall_ratings'], dict):
            raise ValidationError("Recall ratings must be a dictionary.")
        
        canonical.append(entry)
    
    return canonical


@transaction.atomic
def submit_lesson(*, user, session_id, responses):
    session = LessonAttempt.objects.select_for_update().filter(pk=session_id, user=user).first()
    
    if session is None:
        raise ValidationError("Lesson session not found.")
    
    canonical = _canonical_responses(responses)
    
    if session.submitted_at is not None:
        if session.submission != canonical:
            raise ValidationError("This lesson was already submitted with different answers or ratings.")
        return session
    
    exercises = session.exercises
    count = len(exercises)
    
    if not count or not count <= len(canonical) <= count * 2:
        raise ValidationError("Answer each exercise once, followed by optional practice retries.")
    
    if [row['exercise_id'] for row in canonical[:count]] != [row['id'] for row in exercises]:
        raise ValidationError("First answers must cover every delivered exercise in lesson order.")
    
    by_id = {row['id']: row for row in exercises}
    retried, prepared = set(), []
    
    for sequence, item in enumerate(canonical):
        exercise = by_id.get(item['exercise_id'])
        if exercise is None:
            raise ValidationError("An answer refers to an exercise outside this lesson.")
        is_first = sequence < count
        if not is_first:
            # Allow a retry even when the server graded the first answer correct:
            # the client may have graded it wrong. This disagreement stays silent.
            if item['exercise_id'] in retried:
                raise ValidationError("Each exercise may be retried once.")
            retried.add(item['exercise_id'])
        grade = grade_exercise(exercise, item['response'])
        requested = parse_recall_ratings(grade.target_results, item['recall_ratings'])
        effective = {key: (value if next(row for row in grade.target_results if str(row['sense_id']) == key)['score'] == 1 else 1)
                     for key, value in requested.items()}
        prepared.append((sequence, item, grade, effective, is_first))
    
    get_user_model().objects.select_for_update().get(pk=user.pk)
    now = timezone.now()
    seen, scores, results = set(), [], []
    
    for sequence, item, grade, ratings, is_first in prepared:
        answer = ExerciseAttempt.objects.create(
            lesson_attempt=session, exercise_id=item['exercise_id'], sequence=sequence, is_first=is_first,
            response=item['response'], recall_ratings=item['recall_ratings'],
            score=Decimal(str(grade.score)).quantize(Decimal('0.0001')), submitted_at=now,
        )
        
        eligible = [row for row in grade.target_results if row['sense_id'] not in seen] if is_first else []
        
        ids = {str(row['sense_id']) for row in eligible}
        logs = schedule_answer_reviews(answer=answer, target_results=eligible,
                    recall_ratings={key: value for key, value in ratings.items() if key in ids}, reviewed_at=now) if eligible else []
        by_sense = {log.progress.lexeme_sense_id: log for log in logs}
        answer.target_results = [{**row, 'fsrs_eligible': row['sense_id'] in by_sense,
            **({'rating': by_sense[row['sense_id']].rating, 'due': by_sense[row['sense_id']].card_after['due']}
               if row['sense_id'] in by_sense else {})} for row in grade.target_results]
        answer.save(update_fields=['target_results'])
        seen.update(row['sense_id'] for row in eligible)
        
        if is_first:
            scores.append(grade.score)
            results.append({'exercise_id': item['exercise_id'], 'score': grade.score, 'target_results': answer.target_results})
    
    mean = sum(scores) / count
    owner, _ = UserProgress.objects.get_or_create(user=user)
    progress, _ = UserLessonProgress.objects.get_or_create(user_progress=owner, lesson_id=session.lesson_id)
    progress.best_score = max(progress.best_score, int((Decimal(str(mean)) * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP)))
    
    if progress.status != UserLessonProgress.Status.COMPLETED:
        progress.status, progress.completed_at = UserLessonProgress.Status.COMPLETED, now
    
    progress.save(update_fields=['best_score', 'status', 'completed_at'])
    session.submission, session.submitted_at = canonical, now
    session.server_result = {'total': count, 'first_try_correct': sum(score == 1 for score in scores),
                            'mean_score': mean, 'results': results}
    
    session.save(update_fields=['submission', 'submitted_at', 'server_result'])
    
    return session
