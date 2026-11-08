from django.db import models
from django.utils import timezone
from apps.courses.models import Lesson
from django.contrib.auth import get_user_model

User = get_user_model()

# Create your models here.

class UserProgress(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="progress")
    streak = models.PositiveIntegerField(default=0)
    points = models.PositiveIntegerField(default=0)

    
class UserLessonProgress(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = "not_started"
        IN_PROGRESS = "in_progress"
        COMPLETED = "completed"

    user_progress = models.ForeignKey(
        UserProgress,
        on_delete=models.CASCADE,
        related_name="lessons",
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="user_progress",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NOT_STARTED)
    completed_at = models.DateTimeField(null=True, blank=True)

    best_score = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user_progress", "lesson"],
                name="unique_progress_per_user_lesson",
            )
        ]
        
        indexes = [
            models.Index(fields=["user_progress", "status"]),
        ]


    def __str__(self):
        return f"{self.user} - {self.lesson}"

class LexemeProgress(models.Model):
    """One FSRS card per learner and vocabulary sense."""

    class State(models.IntegerChoices):
        LEARNING = 1, "Learning"
        REVIEW = 2, "Review"
        RELEARNING = 3, "Relearning"

    user_progress = models.ForeignKey(UserProgress, on_delete=models.CASCADE, related_name="lexeme_progress")
    lexeme_sense = models.ForeignKey("vocabulary.LexemeSense", on_delete=models.PROTECT, related_name="learner_progress")
    state = models.PositiveSmallIntegerField(choices=State.choices, default=State.LEARNING)
    step = models.PositiveIntegerField(null=True, blank=True, default=0)
    stability = models.FloatField(null=True, blank=True)
    difficulty = models.FloatField(null=True, blank=True)
    reps = models.PositiveIntegerField(default=0)
    lapses = models.PositiveIntegerField(default=0)
    due = models.DateTimeField(default=timezone.now)
    last_review = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user_progress", "lexeme_sense"], name="unique_learner_sense_progress"),
            models.CheckConstraint(condition=models.Q(state__in=[1, 2, 3]), name="fsrs_valid_state"),
            models.CheckConstraint(condition=models.Q(stability__isnull=True) | models.Q(stability__gt=0), name="fsrs_positive_stability"),
            models.CheckConstraint(condition=models.Q(difficulty__isnull=True) | models.Q(difficulty__gte=1, difficulty__lte=10), name="fsrs_difficulty_range"),
            models.CheckConstraint(condition=models.Q(lapses__lte=models.F("reps")), name="fsrs_lapses_range"),
            models.CheckConstraint(condition=(models.Q(state=2, step__isnull=True) | models.Q(state__in=[1, 3], step__isnull=False)), name="fsrs_state_step"),
        ]
        indexes = [models.Index(fields=["user_progress", "due"])]


class LexemeReviewLog(models.Model):
    class Rating(models.IntegerChoices):
        AGAIN = 1, "Again"
        HARD = 2, "Hard"
        GOOD = 3, "Good"
        EASY = 4, "Easy"

    progress = models.ForeignKey(LexemeProgress, on_delete=models.CASCADE, related_name="reviews")
    attempt = models.ForeignKey("exercises.ExerciseAttempt", on_delete=models.RESTRICT, related_name="reviews")
    rating = models.PositiveSmallIntegerField(choices=Rating.choices)
    score = models.DecimalField(max_digits=5, decimal_places=4)
    reviewed_at = models.DateTimeField()
    package_version = models.CharField(max_length=30)
    policy_version = models.CharField(max_length=30, default="exercise-v1")
    scheduler_config = models.JSONField()
    card_before = models.JSONField()
    card_after = models.JSONField()
    fsrs_log = models.JSONField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["attempt", "progress"], name="unique_attempt_sense_review"),
            models.CheckConstraint(condition=models.Q(rating__in=[1, 2, 3, 4]), name="fsrs_review_rating_range"),
            models.CheckConstraint(condition=models.Q(score__gte=0, score__lte=1), name="fsrs_review_score_range"),
        ]
        ordering = ["reviewed_at", "pk"]
