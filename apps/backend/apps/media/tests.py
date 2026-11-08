import pytest
from django.core.exceptions import ValidationError

from apps.media.models import MediaAsset
from apps.vocabulary.models import Expression

pytestmark = pytest.mark.django_db


def test_assets_have_at_most_one_dictionary_subject(learning_language, vocabulary_sense):
    expression = Expression.objects.create(language=learning_language, text="hola", expression_type="phrase")
    with pytest.raises(ValidationError):
        MediaAsset.objects.create(
            storage_key="audio/hola.mp3", media_type="audio", lexeme=vocabulary_sense.lexeme, expression=expression,
        )
    MediaAsset.objects.create(storage_key="images/scene.jpg", media_type="image")
    MediaAsset.objects.create(storage_key="audio/hola.mp3", media_type="audio", lexeme=vocabulary_sense.lexeme)
