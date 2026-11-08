import pytest

from apps.exercises.models import Exercise, ExerciseAcceptedAnswer, ExerciseTarget, PromptBlock
from apps.exercises.services import publish_exercise
from apps.vocabulary.models import Language, Lexeme, LexemeSense


@pytest.fixture
def learning_language(db):
    return Language.objects.create(code="es", name="Spanish")


@pytest.fixture
def vocabulary_sense(learning_language):
    lexeme = Lexeme.objects.create(language=learning_language, lemma="hola", normalized_lemma="hola")
    return LexemeSense.objects.create(lexeme=lexeme, meaning="hello")


@pytest.fixture
def exercise_factory(learning_language, vocabulary_sense):
    def create(exercise_type=Exercise.Type.TRANSLATION, *, with_prompt=True, with_target=True, **kwargs):
        defaults = dict(language=learning_language, exercise_type=exercise_type, level=Exercise.Level.A1,
                        instruction="Complete the exercise")
        defaults.update(kwargs)
        exercise = Exercise.objects.create(**defaults)
        if with_target:
            ExerciseTarget.objects.create(exercise=exercise, sense=vocabulary_sense)
        if with_prompt:
            PromptBlock.objects.create(exercise=exercise, text="Prompt", block_type="text", position=0)
        return exercise
    return create


@pytest.fixture
def published_exercise(exercise_factory):
    exercise = exercise_factory()
    ExerciseAcceptedAnswer.objects.create(exercise=exercise, text="hello", is_primary=True)
    return publish_exercise(exercise.pk)
