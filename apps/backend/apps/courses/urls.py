from django.urls import path, register_converter
from .views import UnitList, LessonView, LessonSubmitView
from .utils import LessonCodeConverter

register_converter(LessonCodeConverter, "lesson_code")

app_name = "apps.courses"

urlpatterns = [
    path('units/', UnitList.as_view(), name='unit-list'),
    path('lesson/<lesson_code:code>/', LessonView.as_view(), name='get-lesson'),
    path('lesson/<lesson_code:code>/submit/', LessonSubmitView.as_view(), name='complete-lesson'),
]