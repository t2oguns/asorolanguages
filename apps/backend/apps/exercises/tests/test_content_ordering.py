import pytest
from django.core.exceptions import ValidationError

from apps.exercises.models import PromptBlock

pytestmark = pytest.mark.django_db


def test_blocks_follow_authored_order(exercise_factory):
    exercise = exercise_factory(with_prompt=False)
    for text, position in (("world", 1), ("Hello", 0)):
        PromptBlock.objects.create(exercise=exercise, block_type="text", text=text, position=position)
    assert list(exercise.prompt_blocks.values_list("text", flat=True)) == ["Hello", "world"]


def test_position_is_unique_within_an_exercise(exercise_factory):
    exercise = exercise_factory()
    with pytest.raises(ValidationError):
        PromptBlock.objects.create(exercise=exercise, block_type="text", text="duplicate", position=0)
    other = exercise_factory()
    assert other.prompt_blocks.get().position == 0
