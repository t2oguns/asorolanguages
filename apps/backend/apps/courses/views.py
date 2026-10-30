from django.shortcuts import render
from rest_framework import generics, permissions
from rest_framework.response import Response
from .models import Unit, Lesson
from .serializers import UnitSerializer, LessonSerializer
from apps.progress.services import get_units, complete_lesson, start_lesson

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
        progress = start_lesson(request.user, instance) # Creates lesson progress object / user progress object
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

class LessonSubmitView(generics.GenericAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    lookup_field = "code"
    lookup_url_kwarg = "code"

    def post(self, request, *args, **kwargs):
        instance = self.get_object()
        progress = complete_lesson(request.user, lesson=instance, score=instance.difficulty)
        
        serializer = self.get_serializer(instance)
        # change to response showing stats?
        return Response(serializer.data)
