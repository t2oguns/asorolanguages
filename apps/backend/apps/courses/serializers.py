from rest_framework import serializers
from .models import Unit, Module, Lesson


class LessonSerializer(serializers.ModelSerializer):
    #slides = SlideSerializer(many=True, read_only=True)

    class Meta:
        model = Lesson
        fields = ["id", "title", "description", "order", "difficulty", "module", "code", ] # "slides"


class LessonDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = Lesson
        fields = ["id", "title", "description", "order", "difficulty", "module", "code"]

class ModuleSerializer(serializers.ModelSerializer):
    lessons = LessonDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = ["id", "unit", "title", "order", "lessons"]


class UnitSerializer(serializers.ModelSerializer):
    modules = ModuleSerializer(many=True, read_only=True)

    class Meta:
        model = Unit
        fields = ["id", "title", "description", "order", "modules"]