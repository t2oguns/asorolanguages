import uuid
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

# Create your models here.


class Language(models.Model):
    """A language or regional variety, identified by a BCP 47 tag."""

    code = models.CharField(max_length=63, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Lexeme(models.Model):
    """A reusable dictionary entry."""

    class PartOfSpeech(models.TextChoices):
        NOUN = "noun", "Noun"
        VERB = "verb", "Verb"
        PRONOUN = "pronoun", "Pronoun"
        ADJECTIVE = "adjective", "Adjective"
        ADVERB = "adverb", "Adverb"
        PARTICLE = "particle", "Particle"
        QUESTION = "question", "Question"
        PREPOSITION = "preposition", "Preposition"
        INTERJECTION = "interjection", "Interjection"
        OTHER = "other", "Other"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    lemma = models.CharField(max_length=255)
    language = models.ForeignKey(Language, on_delete=models.PROTECT, related_name="lexemes")
    normalized_lemma = models.CharField(max_length=255) # Normalized, without diacritics, to allow for search


    part_of_speech = models.CharField(
        max_length=30,
        choices=PartOfSpeech.choices,
        default=PartOfSpeech.OTHER,
    )

    pronunciation_ipa = models.CharField(
        max_length=255, blank=True
    )

    # embedding = VectorField(dimensions=768, null=True, blank=True)


    class Meta:
        indexes = [
            models.Index(fields=["lemma"]),
            models.Index(fields=["normalized_lemma"]),
        ]

    def __str__(self):
        return self.lemma

class LexemeSense(models.Model):
    """A particular meaning of a lexeme."""

    lexeme = models.ForeignKey(
        Lexeme,
        on_delete=models.CASCADE,
        related_name="senses",
    )
    meaning = models.CharField(max_length=255)
    translation = models.CharField(max_length=255, blank=True)

    example = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

class Expression(models.Model):
    """A phrase, sentence, or fixed expression."""

    class ExpressionType(models.TextChoices):
        PHRASE = "phrase", "Phrase"
        SENTENCE = "sentence", "Sentence"
        PASSAGE = "passage", "Passage"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    language = models.ForeignKey(Language, on_delete=models.PROTECT, related_name="expressions")
    text = models.TextField()
    translation = models.TextField(blank=True)
    
    expression_type = models.CharField(
        max_length=20,
        choices=ExpressionType.choices,
    )
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.text[:80]



def validate_expression_span(expression, start, end):
    """Offsets count Python Unicode code points; end is exclusive."""
    if start is not None and end is not None and not (0 <= start < end <= len(expression.text)):
        raise ValidationError("The span must be a nonempty range within the expression.")


class ExpressionToken(models.Model):
    """An ordered segmentation unit; annotations separately describe selected spans."""

    expression = models.ForeignKey(
        Expression,
        on_delete=models.CASCADE,
        related_name="tokens",
    )
    position = models.PositiveIntegerField()
    start_offset = models.PositiveIntegerField()
    end_offset = models.PositiveIntegerField()

    sense = models.ForeignKey(
        LexemeSense,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    translation_override = models.CharField(
        max_length=255,
        blank=True,
    )
    grammar_note = models.TextField(blank=True)

    def clean(self):
        super().clean()
        if self.expression_id:
            validate_expression_span(self.expression, self.start_offset, self.end_offset)
            if self.sense_id and self.sense.lexeme.language_id != self.expression.language_id:
                raise ValidationError({"sense": "The sense must belong to the expression's language."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(
                fields=["expression", "position"],
                name="unique_expression_token_position",
            ),
            models.CheckConstraint(
                condition=Q(end_offset__gt=models.F("start_offset")),
                name="token_valid_offset_range",
            ),
        ]

class ExpressionAnnotation(models.Model):
    """
    Annotates any meaningful span of an expression.

    Supports individual words, multiword phrases,
    grammar patterns, and idiomatic expressions.
    """

    class AnnotationType(models.TextChoices):
        WORD = "word", "Word"
        PHRASE = "phrase", "Phrase"
        IDIOM = "idiom", "Idiom"

    expression = models.ForeignKey(
        Expression,
        on_delete=models.CASCADE,
        related_name="annotations",
    )
    annotation_type = models.CharField(
        max_length=20,
        choices=AnnotationType.choices,
    )
    start_offset = models.PositiveIntegerField()
    end_offset = models.PositiveIntegerField()

    meaning = models.CharField(max_length=500)
    explanation = models.TextField(blank=True)

    # Word meanings reference a precise sense; phrases may reference an expression.

    sense = models.ForeignKey(
        LexemeSense,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    related_expression = models.ForeignKey(
        Expression,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="referenced_annotations",
    )

    def clean(self):
        super().clean()
        if self.expression_id:
            validate_expression_span(self.expression, self.start_offset, self.end_offset)
            if self.sense_id and self.sense.lexeme.language_id != self.expression.language_id:
                raise ValidationError({"sense": "The sense must belong to the expression's language."})
            if self.related_expression_id and self.related_expression.language_id != self.expression.language_id:
                raise ValidationError({"related_expression": "The referenced expression must use the same language."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(end_offset__gt=models.F("start_offset")),
                name="annotation_valid_offset_range",
            ),
            models.CheckConstraint(
                condition=(
                    Q(sense__isnull=False, related_expression__isnull=True)
                    | Q(sense__isnull=True, related_expression__isnull=False)
                ),
                name="annotation_exactly_one_reference",
            ),
            models.CheckConstraint(
                condition=(
                    Q(related_expression__isnull=True)
                    | ~Q(related_expression=models.F("expression"))
                ),
                name="annotation_no_self_reference",
            ),
        ]

