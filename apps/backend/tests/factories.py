from apps.users.models import User
from apps.courses.models import Lesson, Module, Unit
from apps.progress.models import UserProgress, UserLessonProgress

def make_user(**kwargs):
    defaults = {
        "email": "test@example.com",
    }
    defaults.update(kwargs)

    return User.objects.create_user(
        **defaults,
    )

def make_user_progress(**kwargs):
    return UserProgress.objects.create(**kwargs)

def make_unit(**kwargs):
    defaults = {
        "title": "Unit 1",
        "order": 1,
    }
    defaults.update(kwargs)

    return Unit.objects.create(
        **defaults,
    )

def make_module(unit, **kwargs):
    defaults = {
        "title": "Module 1",
        "order": 1,
    }
    defaults.update(kwargs)

    return Module.objects.create(
        unit=unit,
        **defaults,
    )

def make_lesson(module, **kwargs):
    defaults = {
        "title": "Lesson 1",
        "order": 1,
    }
    defaults.update(kwargs)

    return Lesson.objects.create(
        module=module,
        **defaults,
    )

def make_lesson_progress(user_progress, lesson, **kwargs):
    defaults = {
        "status":UserLessonProgress.Status.IN_PROGRESS,
        "completed_at":None,
        "best_score":0,
    }

    defaults.update(kwargs)

    return UserLessonProgress.objects.create(
        user_progress=user_progress,
        lesson=lesson,
        **defaults
    )
