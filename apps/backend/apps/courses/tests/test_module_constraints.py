import pytest
from django.db import IntegrityError

from apps.courses.models import Lesson, Module, Unit
from tests.factories import make_module

def test_unit_cannot_be_null(db):
    with pytest.raises(IntegrityError):
        Module.objects.create(
            title="Standalone module",
            order=1,
            unit=None,
        )
    

def test_modules_are_ordered_by_order(unit):
    module1 = make_module(title="Lesson 1", order=2, unit=unit)
    module2 = make_module(title="Lesson 2", order=1, unit=unit)

    modules = Module.objects.all()
    assert list(modules) == [module2, module1]


def test_module_cannot_have_the_same_order(unit):
    # Attempt to create another module with the same order in the same unit
    make_module(order=1, unit=unit)

    with pytest.raises(IntegrityError):
        Module.objects.create(title="Module 2", order=1, unit=unit)

def test_same_order_is_allowed_in_different_units(unit):
    another_unit = Unit.objects.create(title="Django Basics", order=2)

    module_1 = make_module(
        title="Module One",
        order=1,
        unit=unit,
    )
    module_2 = make_module(
        title="Module Two",
        order=1,
        unit=another_unit,
    )

    assert Module.objects.count() == 2
