from rest_framework import serializers
from .models import Unit, Module, Lesson
from apps.progress.models import UserLessonProgress
from apps.progress.serializers import LessonProgressSerializer

class LessonSerializer(serializers.ModelSerializer):
    #slides = SlideSerializer(many=True, read_only=True)
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ["id", "title", "description", "order", "difficulty", "code", "progress"] # "slides"

    def get_progress(self, lesson):
            # Back reference from service augmentation
            records = lesson.current_user_progress
    
            if not records:
                return {
                    "status": UserLessonProgress.Status.NOT_STARTED,
                    "score": None,
                    "completed_at": None,
                }
            return LessonProgressSerializer(records[0]).data


class LessonDetailSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ["id", "title", "code", "description", "order", "difficulty", "progress"]

    def get_progress(self, lesson):
        # Back reference from service augmentation
        # getattr because becayse current_user_progress is an filtered list, not an actual model field
        records = getattr(lesson, "current_user_progress", [])

        if not records:
            return {
                "status": UserLessonProgress.Status.NOT_STARTED,
                "score": None,
                "completed_at": None,
            }
        return LessonProgressSerializer(records[0]).data

class ModuleSerializer(serializers.ModelSerializer):
    lessons = LessonDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = ["id", "title", "order", "lessons"]


class UnitSerializer(serializers.ModelSerializer):
    modules = ModuleSerializer(many=True, read_only=True)

    class Meta:
        model = Unit
        fields = ["id", "title", "description", "order", "modules"]