from rest_framework import generics
from rest_framework.response import Response
from .models import Lesson
from .serializers import UnitSerializer, LessonSerializer
from apps.progress.services import get_units
from apps.progress.models import UserLessonProgress

# Create your views here.

class UnitList(generics.ListAPIView):
    serializer_class = UnitSerializer

    def get_queryset(self):
        return get_units(user=self.request.user)

class LessonView(generics.RetrieveAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    lookup_field = "code"
    lookup_url_kwarg = "code"

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.current_user_progress = list(UserLessonProgress.objects.filter(
            user_progress__user=request.user, lesson=instance,
        ))
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
