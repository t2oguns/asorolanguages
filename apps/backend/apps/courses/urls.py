from django.urls import path, register_converter
from .views import UnitList, LessonView
from .utils import LessonCodeConverter
from apps.exercises.views import LessonSessionStartView, LessonSessionSubmitView

register_converter(LessonCodeConverter, "lesson_code")

app_name = "apps.courses"

urlpatterns = [
    path('units/', UnitList.as_view(), name='unit-list'),
    path('lesson/<lesson_code:code>/', LessonView.as_view(), name='get-lesson'),
    path('lesson/<lesson_code:code>/sessions/', LessonSessionStartView.as_view(), name='start-lesson-session'),
    path('lesson/<lesson_code:code>/sessions/<uuid:session_id>/submit/', LessonSessionSubmitView.as_view(), name='submit-lesson-session'),
]
