import pytest
from django.db import IntegrityError

from apps.courses.models import Lesson, Module, Unit
from apps.courses.constants import LESSON_ID_LENGTH

@pytest.fixture
def module(db):
    return Module.objects.create(title="Test Module", order=1, unit=Unit.objects.create(title="Test Unit", order=1))


@pytest.fixture
def lesson(module):
    return Lesson.objects.create(
        title="Introduction",
        module=module,
        order=1,
    )

def test_module_cannot_be_null(db):
    try:
        lesson = Lesson.objects.create(
            title="Standalone lesson",
            order=1,
            module=None,
        )
        assert False, "Expected an IntegrityError due to null module."
    except Exception as e:
        assert "violates not-null constraint" in str(e), f"Unexpected error: {e}"
    

def test_lessons_are_ordered_by_order(module):
    lesson1 = Lesson.objects.create(title="Lesson 1", order=2, module=module)
    lesson2 = Lesson.objects.create(title="Lesson 2", order=1, module=module)

    lessons = Lesson.objects.all()
    assert list(lessons) == [lesson2, lesson1]


def test_lessons_cannot_have_the_same_order(module):
    # Create a lesson with order 1
    Lesson.objects.create(title="Lesson 1", order=1, module=module)

    # Attempt to create another lesson with the same order in the same module
    try:
        Lesson.objects.create(title="Lesson 2", order=1, module=module)
        assert False, "Expected an IntegrityError due to unique constraint violation."
    except Exception as e:
        assert "unique_lesson_order" in str(e), f"Unexpected error: {e}"

def test_same_order_is_allowed_in_different_modules(module):
    another_module = Module.objects.create(title="Django Basics", unit=module.unit, order=2)

    Lesson.objects.create(
        title="Lesson One",
        order=1,
        module=module,
    )
    Lesson.objects.create(
        title="Lesson Two",
        order=1,
        module=another_module,
    )

    assert Lesson.objects.count() == 2

def test_lesson_generates_code(module):
    lesson = Lesson.objects.create(
        title="Introduction",
        module=module,
        order=1,
    )

    assert lesson.code


def test_lesson_code_has_standard_length(module):
    lesson = Lesson.objects.create(
        title="Introduction",
        module=module,
        order=1,
    )

    assert len(lesson.code) == LESSON_ID_LENGTH

