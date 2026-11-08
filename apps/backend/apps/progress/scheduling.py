"""FSRS scheduling for server-graded evidence, independently of exercise graders."""
from datetime import timezone as datetime_timezone
from decimal import Decimal
from importlib.metadata import version

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from fsrs import Card, Rating, Scheduler, State

from apps.progress.models import LexemeProgress, LexemeReviewLog, UserProgress

POLICY_VERSION = "exercise-v1"
PACKAGE_VERSION = version("fsrs")


def scheduler():
    return Scheduler(
        desired_retention=getattr(settings, "FSRS_DESIRED_RETENTION", 0.9),
        enable_fuzzing=getattr(settings, "FSRS_ENABLE_FUZZING", True),
    )


def parse_recall_ratings(target_results, recall_ratings):
    if recall_ratings is None:
        return {}
    if not isinstance(recall_ratings, dict):
        raise ValidationError("Recall ratings must map sense ID strings to ratings 1 through 4.")
    allowed = {str(result["sense_id"]) for result in target_results}
    if any(not isinstance(key, str) or key not in allowed for key in recall_ratings):
        raise ValidationError("Recall ratings must refer to senses assessed by this attempt.")
    if any(type(value) is not int or value not in (1, 2, 3, 4) for value in recall_ratings.values()):
        raise ValidationError("Use Again=1, Hard=2, Good=3 or Easy=4.")
    return recall_ratings


def _card(progress):
    return Card(
        card_id=progress.pk, state=State(progress.state), step=progress.step,
        stability=progress.stability, difficulty=progress.difficulty,
        due=progress.due.astimezone(datetime_timezone.utc),
        last_review=progress.last_review.astimezone(datetime_timezone.utc) if progress.last_review else None,
    )


@transaction.atomic
def schedule_answer_reviews(*, answer, target_results, recall_ratings=None, reviewed_at=None):
    """Internal service: target_results must come from the server grader."""
    get_user_model().objects.select_for_update().get(pk=answer.lesson_attempt.user_id)
    requested = parse_recall_ratings(target_results, recall_ratings)
    owner, _ = UserProgress.objects.get_or_create(user_id=answer.lesson_attempt.user_id)
    engine = scheduler()
    now = (reviewed_at or timezone.now()).astimezone(datetime_timezone.utc)
    logs = []
    for result in sorted(target_results, key=lambda row: int(row["sense_id"])):
        sense_id = result["sense_id"]
        score = result["score"]
        rating = Rating(requested.get(str(sense_id), Rating.Good if score == 1 else Rating.Again))
        if score < 1 and rating != Rating.Again:
            raise ValidationError("Failed or partial recall must be rated Again.")
        progress, _ = LexemeProgress.objects.select_for_update().get_or_create(
            user_progress=owner, lexeme_sense_id=sense_id,
        )
        existing = LexemeReviewLog.objects.filter(progress=progress, attempt=answer).first()
        if existing:
            if existing.rating != rating or existing.score != Decimal(str(score)).quantize(Decimal("0.0001")):
                raise ValidationError("This sense has already been scheduled for the attempt.")
            logs.append(existing)
            continue
        card = _card(progress)
        if card.last_review is not None and now < card.last_review:
            raise ValidationError("A review cannot precede the previous review.")
        before = card.to_dict()
        updated, native_log = engine.review_card(card, rating, review_datetime=now)
        progress.state, progress.step = updated.state.value, updated.step
        progress.stability, progress.difficulty = updated.stability, updated.difficulty
        progress.due, progress.last_review = updated.due, updated.last_review
        progress.reps += 1
        progress.lapses += int(card.state == State.Review and rating == Rating.Again)
        progress.save()
        logs.append(LexemeReviewLog.objects.create(
            progress=progress, attempt=answer, rating=rating.value,
            score=Decimal(str(score)).quantize(Decimal("0.0001")), reviewed_at=now,
            package_version=PACKAGE_VERSION, policy_version=POLICY_VERSION,
            scheduler_config=engine.to_dict(), card_before=before, card_after=updated.to_dict(),
            fsrs_log=native_log.to_dict(),
        ))
    return logs


def due_lexeme_progress(*, user, at=None, language_id=None, limit=50):
    """Reviewed/introduced senses due for practice; unseen senses are not cards yet."""
    if type(limit) is not int or not 1 <= limit <= 200:
        raise ValidationError("The review limit must be between 1 and 200.")
    rows = LexemeProgress.objects.filter(user_progress__user=user, due__lte=at or timezone.now())
    if language_id is not None:
        rows = rows.filter(lexeme_sense__lexeme__language_id=language_id)
    return rows.select_related("lexeme_sense__lexeme").order_by("due", "pk")[:limit]
