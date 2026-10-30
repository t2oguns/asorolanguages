from django.db import transaction
from django.db.models import Prefetch
from apps.progress.models import UserLessonProgress, UserProgress
from apps.courses.models import Unit, Module, Lesson, PUBLISH_STATUS
from django.utils import timezone

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

@transaction.atomic
def start_lesson(user, lesson):
    """ function maybe useful in the future to log repeated lesson starts"""
    user_progress, _ = UserProgress.objects.get_or_create(
        user=user
    )

    lesson_progress, _ = UserLessonProgress.objects.get_or_create(
        user_progress=user_progress,
        lesson=lesson,
        defaults={
            "status": UserLessonProgress.Status.IN_PROGRESS,
        },
    )

    return lesson_progress

def handle_scoring(lesson: Lesson):
    return lesson.difficulty

@transaction.atomic
def complete_lesson(user, lesson):
    #eventually handle scoring in another method

    user_progress, _ = UserProgress.objects.get_or_create(user=user)

    score = handle_scoring(lesson)

    lesson_progress, created = UserLessonProgress.objects.get_or_create(
        user_progress=user_progress,
        lesson=lesson,
        defaults={
            "status": UserLessonProgress.Status.COMPLETED,
            "completed_at": timezone.now(),
            "best_score": score 
        }   
    )

    if not created:
        fields_to_update = []

        # Preserve the highest score.
        if (lesson_progress.best_score is None or score > lesson_progress.best_score):
            lesson_progress.best_score = score
            fields_to_update.append("best_score")

        # Complete the lesson if it wasn't completed yet.
        if lesson_progress.status != UserLessonProgress.Status.COMPLETED:
            lesson_progress.status = UserLessonProgress.Status.COMPLETED
            lesson_progress.completed_at = timezone.now()
            fields_to_update.extend([
                "status",
                "completed_at",
            ])

        if fields_to_update:
            lesson_progress.save(update_fields=fields_to_update)
        

    return lesson_progress