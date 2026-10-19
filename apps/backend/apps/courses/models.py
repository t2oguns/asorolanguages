from django.db import models
from .constants import LESSON_ID_LENGTH
from shortuuid.django_fields import ShortUUIDField

# Create your models here.


class Unit(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ["order"]

class Module(models.Model):
    """
    Modules are the individual subjects in a unit. They house the lessons.
    """

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="modules")
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ["order"]

        constraints = [
            models.UniqueConstraint(
                fields=["unit", "order"],
                name="unique_module_order"
            )
        ]

class PUBLISH_STATUS(models.TextChoices):
    DRAFT ="draft", "Draft"
    GENERATED ="generated", "Generated"
    IN_REVIEW ="in_review", "In Review"
    PUBLISHED    ="published", "Published"
    ARCHIVED ="archived", "Archived"


class Lesson(models.Model):
    """
    Lessons are the individual learning materials in a module. They can be videos, articles, quizzes
    """

    title = models.CharField(max_length=255)
    code = ShortUUIDField(
        length=LESSON_ID_LENGTH,
        max_length=LESSON_ID_LENGTH,
        unique=True,
        editable=False,
    )

    description = models.TextField(blank=True)

    # --TODO -- Change this to a more sophisticated method of difficulty rating
    difficulty = models.PositiveIntegerField(default=1)

    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="lessons")

    # Ordering for lessons within a module.
    order = models.PositiveIntegerField()

    # Whether the lesson is in review, published, or archived. This is important for the content management system.
    publication_status = models.CharField(
        max_length=50,
        choices=PUBLISH_STATUS.choices,
        default=PUBLISH_STATUS.DRAFT,
    )

    def __str__(self):
        return str("Lesson - " + self.title)

    class Meta:
        ordering = ["order"]

        constraints = [
            models.UniqueConstraint(
                fields=["module", "order"],
                name="unique_lesson_order"
            )
        ]


