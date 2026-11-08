import pytest
from django.core.exceptions import ValidationError

from apps.vocabulary.models import Expression, ExpressionAnnotation, ExpressionToken, Language, Lexeme, LexemeSense

pytestmark = pytest.mark.django_db


@pytest.fixture
def expression(learning_language):
    return Expression.objects.create(language=learning_language, expression_type="sentence", text="hola mundo")


def test_same_spelling_can_belong_to_different_languages():
    english = Language.objects.create(code="en", name="English")
    german = Language.objects.create(code="de", name="German")
    for language in (english, german):
        Lexeme.objects.create(language=language, lemma="Gift", normalized_lemma="gift")
    assert Lexeme.objects.filter(language=german).count() == 1


@pytest.mark.parametrize("span_type", ["token", "annotation"])
def test_spans_reject_out_of_bounds_ranges(expression, vocabulary_sense, span_type):
    with pytest.raises(ValidationError):
        if span_type == "token":
            ExpressionToken.objects.create(expression=expression, position=0, start_offset=0, end_offset=99)
        else:
            ExpressionAnnotation.objects.create(
                expression=expression, annotation_type="word", sense=vocabulary_sense,
                meaning="hello", start_offset=0, end_offset=99,
            )


def test_annotation_identifies_a_specific_meaning(expression, vocabulary_sense):
    annotation = ExpressionAnnotation.objects.create(
        expression=expression, annotation_type="word", sense=vocabulary_sense,
        meaning="hello", start_offset=0, end_offset=4,
    )
    assert annotation.sense_id == vocabulary_sense.pk
    with pytest.raises(ValidationError):
        ExpressionAnnotation.objects.create(
            expression=expression, annotation_type="word", sense=vocabulary_sense,
            related_expression=expression, meaning="hello", start_offset=0, end_offset=4,
        )


def test_token_sense_must_use_expression_language(expression):
    english = Language.objects.create(code="en", name="English")
    lexeme = Lexeme.objects.create(language=english, lemma="hello", normalized_lemma="hello")
    sense = LexemeSense.objects.create(lexeme=lexeme, meaning="a greeting")
    with pytest.raises(ValidationError):
        ExpressionToken.objects.create(expression=expression, position=0, start_offset=0, end_offset=4, sense=sense)
