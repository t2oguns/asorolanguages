from django.db.models import Prefetch
from apps.progress.models import UserLessonProgress
from apps.courses.models import Unit, Module, Lesson, PUBLISH_STATUS

def get_units(user):
    user_lessons = UserLessonProgress.objects.filter(user_progress__user=user)

    # Distinct because this query can return the same unit multiple times
    units = Unit.objects.filter(modules__lessons__publication_status=PUBLISH_STATUS.PUBLISHED).distinct().order_by("order").prefetch_related(
        Prefetch(
            "modules",
            queryset=Module.objects.prefetch_related(Prefetch(
                "lessons", 
                queryset=Lesson.objects.filter(publication_status=PUBLISH_STATUS.PUBLISHED).prefetch_related(Prefetch(
                    "user_progress",
                    queryset=user_lessons,
                    to_attr="current_user_progress"
                ))
            ))
        )
    )

    return units
