import pytest
from django.db import IntegrityError

from apps.courses.models import Lesson, Module, Unit

@pytest.fixture
def unit(db):
    return Unit.objects.create(title="Test Unit", order=1)


@pytest.fixture
def module(unit):
    return Module.objects.create(
        title="Introduction",
        unit=unit,
        order=1,
    )

def test_unit_cannot_be_null(db):
    try:
        module = Module.objects.create(
            title="Standalone module",
            order=1,
            unit=None,
        )
        assert False, "Expected an IntegrityError due to null unit."
    except Exception as e:
        assert "violates not-null constraint" in str(e), f"Unexpected error: {e}"
    

def test_modules_are_ordered_by_order(unit):
    module1 = Module.objects.create(title="Lesson 1", order=2, unit=unit)
    module2 = Module.objects.create(title="Lesson 2", order=1, unit=unit)

    modules = Module.objects.all()
    assert list(modules) == [module2, module1]


def test_module_cannot_have_the_same_order(unit, module):
    # Attempt to create another module with the same order in the same unit
    try:
        Module.objects.create(title="Module 2", order=1, unit=unit)
        assert False, "Expected an IntegrityError due to unique constraint violation."
    except Exception as e:
        assert "unique_module_order" in str(e), f"Unexpected error: {e}"

def test_same_order_is_allowed_in_different_units(unit):
    another_unit = Unit.objects.create(title="Django Basics", order=2)

    Module.objects.create(
        title="Module One",
        order=1,
        unit=unit,
    )
    Module.objects.create(
        title="Module Two",
        order=1,
        unit=another_unit,
    )

    assert Module.objects.count() == 2