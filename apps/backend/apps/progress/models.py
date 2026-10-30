from django.db import models
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