from django.urls import path, register_converter
from .views import UnitList, LessonView
#from .utils import LessonCodeConverter

#register_converter(LessonCodeConverter, "lesson_code")

#app_name = "apps.courses"

urlpatterns = [
    path('units/', UnitList.as_view(), name='unit-list'),
#    path('lesson/<lesson_code:code>/', LessonView.as_view(), name='get-lesson')
]