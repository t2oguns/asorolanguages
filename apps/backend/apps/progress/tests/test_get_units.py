import pytest
from apps.courses.models import Unit, Module, Lesson, PUBLISH_STATUS
from apps.progress.services import get_units
from apps.progress.models import UserProgress, UserLessonProgress
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture()
def unit(db):
    return Unit.objects.create(title="Unit 1")

@pytest.fixture()
def module(unit):
    return Module.objects.create(title="Module 1", unit=unit)

@pytest.fixture()
def lesson(module):
    return Lesson.objects.create(title="Lesson 1", module=module, publication_status=PUBLISH_STATUS.PUBLISHED)

"""Tests"""

def test_empty_units_returns_empty_list(unit, user):
    units = get_units(user=user)

    assert not units.exists()

def test_returns_units_with_published_lessons(lesson, user):
    units = get_units(user=user)

    assert units.exists()


def test_excludes_units_without_published_lessons(module, user):
    units = get_units(user=user)
    lesson = Lesson.objects.create(
        title="Lesson 2", 
        module=module, 
        publication_status=PUBLISH_STATUS.DRAFT
    )
    
    assert not units.exists()

def test_returns_each_unit_only_once(unit, module, lesson, user):
    lesson_2 = Lesson.objects.create(
        title="Lesson 2", 
        module=Module.objects.create(title="Title", unit=unit, order=2), 
        publication_status=PUBLISH_STATUS.PUBLISHED,
        order=1
    )
    lesson_3 = Lesson.objects.create(
        title="Lesson 3", 
        module=Module.objects.create(title="Title", unit=unit, order=3),
        publication_status=PUBLISH_STATUS.PUBLISHED,
        order=2
    )
    
    units = list(get_units(user=user))

    assert len(units) == 1
    assert units[0] == unit


def test_orders_units_by_order(user, unit):
    
    unit_later = Unit.objects.create(order=20)
    unit_first = Unit.objects.create(order=1)
    unit_middle = Unit.objects.create(order=10)

    for iter in (unit_later, unit_first, unit_middle):
        Lesson.objects.create(
            module=Module.objects.create(title="Title", unit=iter), 
            publication_status=PUBLISH_STATUS.PUBLISHED
        )

    result = list(get_units(user))

    assert result == [unit_first, unit_middle, unit_later]
    

def test_attaches_only_requested_users_progress(lesson, user):
    user2 = User.objects.create(email="other@example.com")

    user_progress_1 = UserProgress.objects.create(user=user)
    user_progress_2 = UserProgress.objects.create(user=user2)

    units = get_units(user)

    expected = UserLessonProgress.objects.create(
        lesson=lesson,
        user_progress=user_progress_1,
    )

    other = UserLessonProgress.objects.create(
        lesson=lesson,
        user_progress=user_progress_2,
    )

    result = list(get_units(user))
    result_lesson = list(result[0].modules.all()[0].lessons.all())[0]

    assert result_lesson.current_user_progress == [expected]


def test_lesson_without_progress_has_empty_progress_list(module, lesson, user):

    progress = UserProgress.objects.create(user=user)
    
    units = get_units(user)

    result = list(units)
    
    result_lesson = list(result[0].modules.all()[0].lessons.all())[0]

    assert result_lesson == lesson
    assert result_lesson.current_user_progress == []


def test_prefetches_nested_relationships_without_extra_queries(
    user, unit, module, lesson
):
    # Evaluate the queryset and all prefetches first.
    units = list(get_units(user))

    with CaptureQueriesContext(connection) as queries:
        for unit in units:
            for module in unit.modules.all():
                for lesson in module.lessons.all():
                    list(lesson.current_user_progress)

    assert len(queries) == 0

def test_empty_result_does_not_raise_errors(user):
    result = list(get_units(user))

    assert result == []