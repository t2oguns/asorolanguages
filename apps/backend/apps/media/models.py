import uuid

from django.db import models
from django.db.models import Q
from apps.vocabulary.models import Expression, Lexeme, Language

# Create your models here.


class MediaAsset(models.Model):
    class Type(models.TextChoices):
        AUDIO = "audio", "Audio"
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    media_type = models.CharField(
        max_length=10,
        choices=Type.choices,
    )

    # S3 object key, NOT a CloudFront URL
    storage_key = models.CharField(
        max_length=1024,
        unique=True,
    )

    title = models.CharField(max_length=255, blank=True)
    alt_text = models.TextField(blank=True)

    transcript = models.TextField(blank=True)
    language = models.ForeignKey(
        Language, on_delete=models.PROTECT, null=True, blank=True,
        related_name="media_assets",
    )

    lexeme = models.ForeignKey(
        Lexeme,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="media_assets",
    )

    expression = models.ForeignKey(
        Expression,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="media_assets",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(lexeme__isnull=True) | Q(expression__isnull=True),
                name="media_at_most_one_vocabulary_reference",
            ),
        ]

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.title or self.storage_key

