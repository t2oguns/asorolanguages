import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import models, transaction
from django.db.models import F, Q

from apps.courses.models import Lesson
from apps.media.models import MediaAsset
from apps.vocabulary.models import Expression, Language, LexemeSense


class AuthoredQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError("Use authoring saves instead of bulk updates.")

    def delete(self):
        raise ValidationError("Use authoring deletes instead of bulk deletion.")

    def bulk_create(self, objs, **kwargs):
        raise ValidationError("Bulk creation bypasses authoring validation.")

    def bulk_update(self, objs, fields, **kwargs):
        raise ValidationError("Bulk updates bypass authoring validation.")


class Exercise(models.Model):
    class Type(models.TextChoices):
        MULTIPLE_CHOICE = "multiple_choice", "Multiple Choice"
        FILL_BLANK = "fill_blank", "Fill Blank"
        TRANSLATION = "translation", "Translation"
        WORD_ORDER = "word_order", "Word Order"
        MATCHING = "matching", "Matching"
        ERROR_CORRECTION = "error_correction", "Error Correction"

    class Level(models.TextChoices):
        A1 = "A1", "A1"
        A2 = "A2", "A2"
        B1 = "B1", "B1"
        B2 = "B2", "B2"
        C1 = "C1", "C1"
        C2 = "C2", "C2"

    objects = AuthoredQuerySet.as_manager()
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lessons = models.ManyToManyField(Lesson, through="LessonExercise", related_name="exercises")
    language = models.ForeignKey(Language, on_delete=models.PROTECT)
    exercise_type = models.CharField(max_length=30, choices=Type.choices)
    instruction = models.TextField()
    explanation = models.TextField(blank=True)
    explanation_media = models.ForeignKey(MediaAsset, on_delete=models.PROTECT, null=True, blank=True)
    level = models.CharField(max_length=2, choices=Level.choices)
    case_sensitive = models.BooleanField(default=False)
    ignore_punctuation = models.BooleanField(default=False)
    ignore_diacritics = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @transaction.atomic
    def save(self, *args, **kwargs):
        existing = type(self).objects.select_for_update().filter(pk=self.pk).first()
        if existing and existing.is_published:
            raise ValidationError("Unpublish the exercise before editing it.")
        if self.is_published or self.published_at is not None:
            raise ValidationError("Publish through publish_exercise().")
        self.full_clean()
        return super().save(*args, **kwargs)

    @transaction.atomic
    def delete(self, *args, **kwargs):
        if type(self).objects.select_for_update().filter(pk=self.pk, is_published=True).exists():
            raise ValidationError("Unpublish the exercise before deleting it.")
        return super().delete(*args, **kwargs)


class LessonExercise(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="exercise_placements")
    exercise = models.ForeignKey(Exercise, on_delete=models.PROTECT, related_name="lesson_placements")
    position = models.PositiveIntegerField()

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(fields=["lesson", "position"], name="unique_lesson_exercise_position"),
            models.UniqueConstraint(fields=["lesson", "exercise"], name="unique_lesson_exercise"),
        ]


class ExerciseChild(models.Model):
    objects = AuthoredQuerySet.as_manager()
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)

    class Meta:
        abstract = True

    def lock_exercise(self):
        ids = {self.exercise_id}
        if self.pk:
            ids.update(type(self).objects.filter(pk=self.pk).values_list("exercise_id", flat=True))
        if any(row.is_published for row in Exercise.objects.select_for_update().filter(pk__in=ids).order_by("pk")):
            raise ValidationError("Unpublish the exercise before editing its content or answers.")

    @transaction.atomic
    def save(self, *args, **kwargs):
        self.lock_exercise()
        self.full_clean()
        return super().save(*args, **kwargs)

    @transaction.atomic
    def delete(self, *args, **kwargs):
        self.lock_exercise()
        return super().delete(*args, **kwargs)


class ExerciseTarget(ExerciseChild):
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name="targets")
    sense = models.ForeignKey(LexemeSense, on_delete=models.PROTECT)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["exercise", "sense"], name="unique_exercise_target_sense")]

    def clean(self):
        super().clean()
        if self.sense_id and self.exercise_id and self.sense.lexeme.language_id != self.exercise.language_id:
            raise ValidationError({"sense": "The target must use the exercise's learning language."})


class PromptBlock(ExerciseChild):
    class Type(models.TextChoices):
        TEXT = "text", "Text"
        WORD = "word", "Word"
        EXPRESSION = "expression", "Expression"
        MEDIA = "media", "Media"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name="prompt_blocks")
    position = models.PositiveIntegerField()
    block_type = models.CharField(max_length=20, choices=Type.choices)
    text = models.TextField(blank=True)
    lexeme_sense = models.ForeignKey(LexemeSense, on_delete=models.PROTECT, null=True, blank=True)
    expression = models.ForeignKey(Expression, on_delete=models.PROTECT, null=True, blank=True)
    media = models.ForeignKey(MediaAsset, on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(fields=["exercise", "position"], name="unique_prompt_block_position"),
            models.CheckConstraint(condition=(
                Q(block_type="text", lexeme_sense__isnull=True, expression__isnull=True, media__isnull=True) & ~Q(text="")
                | Q(block_type="word", text="", lexeme_sense__isnull=False, expression__isnull=True, media__isnull=True)
                | Q(block_type="expression", text="", lexeme_sense__isnull=True, expression__isnull=False, media__isnull=True)
                | Q(block_type="media", text="", lexeme_sense__isnull=True, expression__isnull=True, media__isnull=False)
            ), name="valid_prompt_block_source"),
        ]

    def clean(self):
        super().clean()
        sources = {"text": bool(self.text.strip()), "word": bool(self.lexeme_sense_id),
                   "expression": bool(self.expression_id), "media": bool(self.media_id)}
        if not sources.get(self.block_type) or sum(sources.values()) != 1:
            raise ValidationError("Provide exactly the source selected by block_type.")

    @property
    def source_text(self):
        if self.block_type == self.Type.TEXT:
            return self.text
        if self.block_type == self.Type.EXPRESSION:
            return self.expression.text
        if self.block_type == self.Type.WORD:
            return self.lexeme_sense.lexeme.lemma
        raise ValidationError("A media block does not contain source text.")


class ExerciseOption(ExerciseChild):
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name="options")
    text = models.TextField(blank=True)
    media = models.ForeignKey(MediaAsset, on_delete=models.PROTECT, null=True, blank=True)
    position = models.PositiveIntegerField()
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(fields=["exercise", "position"], name="unique_option_position"),
            models.CheckConstraint(condition=~Q(text="") | Q(media__isnull=False), name="option_has_content"),
        ]

    def clean(self):
        if not self.text.strip() and not self.media_id:
            raise ValidationError("An option needs text or media.")


class ExerciseAcceptedAnswer(ExerciseChild):
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name="accepted_answers")
    text = models.TextField()
    is_primary = models.BooleanField(default=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["exercise"], condition=Q(is_primary=True), name="unique_primary_accepted_answer_per_exercise")]

    def clean(self):
        if not self.text.strip():
            raise ValidationError("An accepted answer cannot be blank.")


class TargetedChild(ExerciseChild):
    target = models.ForeignKey(ExerciseTarget, on_delete=models.RESTRICT, null=True, blank=True)

    class Meta:
        abstract = True

    def clean(self):
        super().clean()
        if self.target_id and self.target.exercise_id != self.exercise_id:
            raise ValidationError({"target": "The target must belong to this exercise."})


class ExerciseMatchingPair(TargetedChild):
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name="matching_pairs")
    left_text = models.TextField(blank=True)
    left_media = models.ForeignKey(MediaAsset, on_delete=models.PROTECT, null=True, blank=True, related_name="matching_left_uses")
    right_text = models.TextField(blank=True)
    right_media = models.ForeignKey(MediaAsset, on_delete=models.PROTECT, null=True, blank=True, related_name="matching_right_uses")
    position = models.PositiveIntegerField()

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(fields=["exercise", "position"], name="unique_matching_pair_position"),
            models.CheckConstraint(condition=~Q(left_text="") | Q(left_media__isnull=False), name="matching_left_has_content"),
            models.CheckConstraint(condition=~Q(right_text="") | Q(right_media__isnull=False), name="matching_right_has_content"),
        ]

    def clean(self):
        super().clean()
        if (not self.left_text.strip() and not self.left_media_id) or (not self.right_text.strip() and not self.right_media_id):
            raise ValidationError("Both sides need text or media.")


class ExerciseFillBlankSlot(TargetedChild):
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name="fill_blank_slots")
    source_block = models.ForeignKey(PromptBlock, on_delete=models.RESTRICT, related_name="blank_slots")
    explanation = models.TextField(blank=True)
    position = models.PositiveIntegerField()
    start_offset = models.PositiveIntegerField()
    end_offset = models.PositiveIntegerField()

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(fields=["exercise", "position"], name="unique_exercise_slot_position"),
            models.CheckConstraint(condition=Q(end_offset__gt=F("start_offset")), name="valid_fill_blank_slot_offsets"),
        ]

    def clean(self):
        super().clean()
        if not self.source_block_id or not self.exercise_id:
            return
        if self.source_block.exercise_id != self.exercise_id or self.source_block.block_type not in {"text", "expression"}:
            raise ValidationError("Blanks require a text or expression block in their own prompt.")
        if self.end_offset is not None and self.end_offset > len(self.source_block.source_text):
            raise ValidationError("The blank extends beyond the source text.")
        if type(self).objects.filter(source_block_id=self.source_block_id, start_offset__lt=self.end_offset,
                                     end_offset__gt=self.start_offset).exclude(pk=self.pk).exists():
            raise ValidationError("Blank ranges must not overlap in the same block.")

    @property
    def expected_text(self):
        return self.source_block.source_text[self.start_offset:self.end_offset]


class BlankAcceptedAnswer(models.Model):
    objects = AuthoredQuerySet.as_manager()
    slot = models.ForeignKey(ExerciseFillBlankSlot, on_delete=models.CASCADE, related_name="accepted_answers")
    text = models.TextField()

    def lock_slots(self):
        ids = {self.slot_id}
        if self.pk:
            ids.update(type(self).objects.filter(pk=self.pk).values_list("slot_id", flat=True))
        for slot in ExerciseFillBlankSlot.objects.filter(pk__in=ids).order_by("exercise_id"):
            slot.lock_exercise()

    @transaction.atomic
    def save(self, *args, **kwargs):
        self.lock_slots()
        self.full_clean()
        return super().save(*args, **kwargs)

    @transaction.atomic
    def delete(self, *args, **kwargs):
        self.lock_slots()
        return super().delete(*args, **kwargs)

    def clean(self):
        if not self.text.strip():
            raise ValidationError("An accepted answer cannot be blank.")


class LessonAttempt(models.Model):
    """One frozen lesson delivery and its atomic, retryable answer submission."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lesson_attempts")
    lesson = models.ForeignKey(Lesson, on_delete=models.PROTECT, related_name="attempts")
    lesson_snapshot = models.JSONField()
    exercises = models.JSONField(default=list)
    submission = models.JSONField(null=True, blank=True)
    server_result = models.JSONField(default=dict)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)


class ExerciseAttempt(models.Model):
    """A submitted answer, including practice retries; no delivery-time child rows."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson_attempt = models.ForeignKey(LessonAttempt, on_delete=models.CASCADE, related_name="answers")
    exercise = models.ForeignKey(Exercise, on_delete=models.PROTECT, related_name="attempts")
    sequence = models.PositiveIntegerField()
    is_first = models.BooleanField(default=True)
    response = models.JSONField()
    recall_ratings = models.JSONField(default=dict)
    score = models.DecimalField(max_digits=5, decimal_places=4)
    target_results = models.JSONField(default=list)
    submitted_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["sequence"]
        constraints = [
            models.UniqueConstraint(fields=["lesson_attempt", "sequence"], name="unique_answer_sequence"),
            models.UniqueConstraint(fields=["lesson_attempt", "exercise"], condition=Q(is_first=True), name="unique_first_exercise_answer"),
            models.CheckConstraint(condition=Q(score__gte=0, score__lte=1), name="attempt_score_range"),
        ]
