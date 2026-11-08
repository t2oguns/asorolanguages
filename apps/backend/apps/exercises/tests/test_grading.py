from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.exercises.grading import grade_exercise
from apps.exercises.lessons import deliver_lesson, submit_lesson
from apps.exercises.models import (
    BlankAcceptedAnswer, Exercise, ExerciseAcceptedAnswer, ExerciseAttempt, ExerciseFillBlankSlot,
    ExerciseMatchingPair, ExerciseOption, ExerciseTarget, LessonExercise, PromptBlock,
)
from apps.exercises.services import publish_exercise, unpublish_exercise
from apps.media.models import MediaAsset
from apps.progress.models import LexemeProgress, LexemeReviewLog
from apps.vocabulary.models import Expression, LexemeSense

pytestmark = pytest.mark.django_db


def deliver(user, lesson, exercise):
    publish_exercise(exercise.pk)
    LessonExercise.objects.create(lesson=lesson, exercise=exercise, position=0)
    return deliver_lesson(user=user, lesson=lesson)


def submit(user, session, response):
    submit_lesson(user=user, session_id=session.pk, responses=[{'exercise_id': session.exercises[0]['id'], 'response': response}])
    return session.answers.get()


@pytest.mark.parametrize('kind', Exercise.Type.values)
def test_every_exercise_type_delivers_model_data_and_grades(user, lesson, exercise_factory, kind):
    exercise = exercise_factory(kind)
    if kind == 'multiple_choice':
        first = ExerciseOption.objects.create(exercise=exercise, text='hello', position=0, is_correct=True)
        ExerciseOption.objects.create(exercise=exercise, text='wrong', position=1)
        response = [str(first.pk)]
    elif kind == 'matching':
        pairs = [ExerciseMatchingPair.objects.create(exercise=exercise, position=i, left_text=f'left {i}', right_text=f'right {i}') for i in range(2)]
        response = {str(pair.pk): str(pair.pk) for pair in pairs}
    elif kind == 'fill_blank':
        slot = ExerciseFillBlankSlot.objects.create(exercise=exercise, source_block=exercise.prompt_blocks.get(), position=0, start_offset=0, end_offset=3)
        BlankAcceptedAnswer.objects.create(slot=slot, text='hello')
        response = {str(slot.pk): 'HELLO'}
    else:
        ExerciseAcceptedAnswer.objects.create(exercise=exercise, text='hello')
        response = ['hello'] if kind == 'word_order' else 'HELLO'
    session = deliver(user, lesson, exercise)
    assert session.exercises[0]['exercise_type'] == kind
    assert not ExerciseAttempt.objects.exists()
    result = submit(user, session, response)
    assert result.score == 1
    assert LexemeProgress.objects.get().reps == 1


def test_media_and_resolved_shared_text_are_in_the_exercise_payload(user, lesson, exercise_factory, learning_language):
    asset = MediaAsset.objects.create(storage_key='audio/hello.mp3', media_type='audio', transcript='not needed')
    expression = Expression.objects.create(language=learning_language, text='original', expression_type='sentence')
    exercise = exercise_factory(explanation_media=asset)
    block = exercise.prompt_blocks.get()
    block.block_type, block.text, block.expression = 'expression', '', expression
    block.save()
    PromptBlock.objects.create(exercise=exercise, position=1, block_type='media', media=asset)
    ExerciseAcceptedAnswer.objects.create(exercise=exercise, text='hello')
    session = deliver(user, lesson, exercise)
    data = session.exercises[0]
    assert data['prompt_blocks'][1]['media']['url'].endswith('/audio/hello.mp3')
    assert data['explanation_media']['id'] == str(asset.pk)
    expression.text = 'edited later'
    expression.save()
    assert data['prompt_blocks'][0]['text'] == 'original'
    # The delivered Exercise, not subsequently edited content, is authoritative.
    unpublish_exercise(exercise.pk)
    assert submit(user, session, 'hello').score == 1


def test_partial_blank_grades_schedule_each_sense_independently(user, lesson, exercise_factory, vocabulary_sense):
    exercise = exercise_factory('fill_blank')
    second = LexemeSense.objects.create(lexeme=vocabulary_sense.lexeme, meaning='another sense')
    targets = [exercise.targets.get(), ExerciseTarget.objects.create(exercise=exercise, sense=second)]
    block = exercise.prompt_blocks.get()
    block.text = 'hello world'
    block.save()
    slots = []
    for i, (start, end, text) in enumerate([(0, 5, 'hello'), (6, 11, 'world')]):
        slot = ExerciseFillBlankSlot.objects.create(exercise=exercise, source_block=block, target=targets[i], position=i, start_offset=start, end_offset=end)
        BlankAcceptedAnswer.objects.create(slot=slot, text=text)
        slots.append(slot)
    BlankAcceptedAnswer.objects.create(slot=slots[0], text='hola')
    session = deliver(user, lesson, exercise)
    answer = submit(user, session, {str(slots[0].pk): 'hola', str(slots[1].pk): 'wrong'})
    assert answer.score == Decimal('.5')
    assert LexemeReviewLog.objects.get(progress__lexeme_sense=vocabulary_sense).rating == 3
    assert LexemeReviewLog.objects.get(progress__lexeme_sense=second).rating == 1


def test_invalid_choices_and_missing_tiles_are_rejected(user, lesson, exercise_factory):
    exercise = exercise_factory('multiple_choice')
    option = ExerciseOption.objects.create(exercise=exercise, position=0, text='yes', is_correct=True)
    ExerciseOption.objects.create(exercise=exercise, position=1, text='no')
    session = deliver(user, lesson, exercise)
    for response in [['unknown'], [str(option.pk), str(option.pk)], [option.pk]]:
        with pytest.raises(ValidationError):
            grade_exercise(session.exercises[0], response)
    assert not LexemeProgress.objects.exists()
