import pytest
from django.core.exceptions import ValidationError

from apps.courses.models import Lesson
from apps.exercises.models import (
    BlankAcceptedAnswer, Exercise, ExerciseAcceptedAnswer, ExerciseTarget,
    ExerciseOption, ExerciseMatchingPair, ExerciseFillBlankSlot, LessonExercise, PromptBlock,
)
from apps.exercises.services import publish_exercise, unpublish_exercise
from apps.media.models import MediaAsset
from apps.vocabulary.models import Lexeme, LexemeSense

pytestmark = pytest.mark.django_db


def test_choices_need_correct_option_and_distractor(exercise_factory):
    exercise = exercise_factory(Exercise.Type.MULTIPLE_CHOICE)
    for text, position in (("Hello", 0), ("Goodbye", 1)):
        ExerciseOption.objects.create(exercise=exercise, text=text, position=position)
    with pytest.raises(ValidationError):
        publish_exercise(exercise.pk)
    option = exercise.options.first()
    option.is_correct = True
    option.save()
    assert publish_exercise(exercise.pk).is_published


@pytest.mark.parametrize("exercise_type", Exercise.Type.values)
def test_each_type_requires_answers(exercise_factory, exercise_type):
    exercise = exercise_factory(exercise_type)
    with pytest.raises(ValidationError):
        publish_exercise(exercise.pk)
    exercise.refresh_from_db()
    assert not exercise.is_published


@pytest.mark.parametrize("with_prompt,with_target", [(False, True), (True, False)])
def test_prompt_and_targets_are_required(exercise_factory, with_prompt, with_target):
    exercise = exercise_factory(with_prompt=with_prompt, with_target=with_target)
    ExerciseAcceptedAnswer.objects.create(exercise=exercise, text="hello")
    with pytest.raises(ValidationError):
        publish_exercise(exercise.pk)


def test_cannot_publish_by_ordinary_save(exercise_factory):
    exercise = exercise_factory()
    exercise.is_published = True
    with pytest.raises(ValidationError):
        exercise.save()


def test_unpublish_edit_republish_keeps_identity(published_exercise):
    old_time = published_exercise.published_at
    exercise = unpublish_exercise(published_exercise.pk)
    assert exercise.published_at is None
    exercise.instruction = "New instruction"
    exercise.save()
    block = exercise.prompt_blocks.get()
    block.text = "Buenos días"
    block.save()
    answer = exercise.accepted_answers.get()
    answer.text = "good morning"
    answer.save()
    new = publish_exercise(exercise.pk)
    assert new.pk == published_exercise.pk
    assert new.published_at > old_time
    assert new.prompt_blocks.get().text == "Buenos días"


def test_invalid_republication_stays_unpublished(published_exercise):
    exercise = unpublish_exercise(published_exercise.pk)
    exercise.accepted_answers.get().delete()
    with pytest.raises(ValidationError):
        publish_exercise(exercise.pk)
    exercise.refresh_from_db()
    assert not exercise.is_published


def test_publication_transitions_are_idempotent(published_exercise):
    assert publish_exercise(published_exercise.pk).published_at == published_exercise.published_at
    exercise = unpublish_exercise(published_exercise.pk)
    assert unpublish_exercise(exercise.pk).updated_at == exercise.updated_at


@pytest.mark.parametrize("kind", ["exercise", "answer", "prompt", "target"])
def test_published_content_rejects_save_and_delete(published_exercise, kind):
    obj = {"exercise": published_exercise, "answer": published_exercise.accepted_answers.get(),
           "prompt": published_exercise.prompt_blocks.get(), "target": published_exercise.targets.get()}[kind]
    with pytest.raises(ValidationError):
        obj.save()
    with pytest.raises(ValidationError):
        obj.delete()


def test_published_content_rejects_inserts_and_bulk_changes(published_exercise):
    with pytest.raises(ValidationError):
        ExerciseAcceptedAnswer.objects.create(exercise=published_exercise, text="hi")
    with pytest.raises(ValidationError):
        published_exercise.accepted_answers.update(text="changed")
    with pytest.raises(ValidationError):
        published_exercise.prompt_blocks.all().delete()


def test_shared_lessons_follow_publication(published_exercise, lesson):
    other = Lesson.objects.create(title="Review", module=lesson.module, order=lesson.order + 1)
    for row in (lesson, other):
        LessonExercise.objects.create(lesson=row, exercise=published_exercise, position=0)
    exercise = unpublish_exercise(published_exercise.pk)
    for row in (lesson, other):
        assert not row.exercises.filter(is_published=True).exists()
    exercise.instruction = "Updated"
    exercise.save()
    publish_exercise(exercise.pk)
    for row in (lesson, other):
        assert row.exercises.get(is_published=True).instruction == "Updated"


def test_media_relationships_on_prompts_choices_pairs_and_explanations(exercise_factory):
    asset = MediaAsset.objects.create(media_type="audio", storage_key="hello.mp3")
    exercise = exercise_factory(Exercise.Type.MULTIPLE_CHOICE, explanation_media=asset)
    PromptBlock.objects.create(exercise=exercise, position=1, block_type="media", media=asset)
    ExerciseOption.objects.create(exercise=exercise, position=0, media=asset, is_correct=True)
    ExerciseOption.objects.create(exercise=exercise, position=1, text="Goodbye")
    assert publish_exercise(exercise.pk).is_published
    matching = exercise_factory(Exercise.Type.MATCHING)
    for position, text in enumerate(("hello", "goodbye")):
        ExerciseMatchingPair.objects.create(exercise=matching, position=position, left_text=text, left_media=asset, right_text=text)
    assert publish_exercise(matching.pk).is_published


def test_targets_and_slots_cannot_cross_exercises(exercise_factory):
    first = exercise_factory(Exercise.Type.FILL_BLANK)
    second = exercise_factory(Exercise.Type.FILL_BLANK)
    with pytest.raises(ValidationError):
        ExerciseFillBlankSlot.objects.create(exercise=second, source_block=first.prompt_blocks.get(), position=0, start_offset=0, end_offset=3)
    with pytest.raises(ValidationError):
        ExerciseMatchingPair.objects.create(exercise=second, target=first.targets.get(), left_text="a", right_text="b", position=0)


def test_blanks_have_alternatives_and_block_scoped_ranges(exercise_factory):
    exercise = exercise_factory(Exercise.Type.FILL_BLANK)
    first = exercise.prompt_blocks.get()
    second = PromptBlock.objects.create(exercise=exercise, position=1, block_type="text", text=first.text)
    for position, block in enumerate((first, second)):
        slot = ExerciseFillBlankSlot.objects.create(exercise=exercise, source_block=block, position=position, start_offset=0, end_offset=3)
        BlankAcceptedAnswer.objects.create(slot=slot, text="Pro")
        BlankAcceptedAnswer.objects.create(slot=slot, text="Alternative")
    for block, start, end in ((first, 2, 4), (second, 4, 99)):
        with pytest.raises(ValidationError):
            ExerciseFillBlankSlot.objects.create(exercise=exercise, source_block=block, position=2, start_offset=start, end_offset=end)
    publish_exercise(exercise.pk)
    with pytest.raises(ValidationError):
        BlankAcceptedAnswer.objects.create(slot=exercise.fill_blank_slots.first(), text="new")


def test_multiple_targets_need_explicit_per_item_mapping(exercise_factory, learning_language):
    exercise = exercise_factory(Exercise.Type.FILL_BLANK)
    lexeme = Lexeme.objects.create(language=learning_language, lemma="mundo", normalized_lemma="mundo")
    sense = LexemeSense.objects.create(lexeme=lexeme, meaning="world")
    ExerciseTarget.objects.create(exercise=exercise, sense=sense)
    slot = ExerciseFillBlankSlot.objects.create(exercise=exercise, source_block=exercise.prompt_blocks.get(), position=0, start_offset=0, end_offset=3)
    BlankAcceptedAnswer.objects.create(slot=slot, text="Pro")
    with pytest.raises(ValidationError):
        publish_exercise(exercise.pk)


def test_draft_exercise_and_its_blanks_can_be_deleted(exercise_factory):
    exercise = exercise_factory(Exercise.Type.FILL_BLANK)
    slot = ExerciseFillBlankSlot.objects.create(exercise=exercise, source_block=exercise.prompt_blocks.get(), position=0, start_offset=0, end_offset=3, target=exercise.targets.get())
    BlankAcceptedAnswer.objects.create(slot=slot, text="Pro")
    exercise.delete()
    assert not Exercise.objects.filter(pk=exercise.pk).exists()


def test_indistinguishable_choices_cannot_be_published(exercise_factory):
    exercise = exercise_factory(Exercise.Type.MULTIPLE_CHOICE)
    for position in range(2):
        ExerciseOption.objects.create(exercise=exercise, position=position, text="same", is_correct=position == 0)
    with pytest.raises(ValidationError, match="distinguishable"):
        publish_exercise(exercise.pk)


def test_indistinguishable_matching_items_cannot_be_published(exercise_factory):
    exercise = exercise_factory(Exercise.Type.MATCHING)
    for position in range(2):
        ExerciseMatchingPair.objects.create(exercise=exercise, position=position, left_text="same", right_text=str(position))
    with pytest.raises(ValidationError, match="distinguishable"):
        publish_exercise(exercise.pk)
