from rest_framework import serializers
from apps.progress.models import UserLessonProgress

class LessonProgressSerializer(serializers.Serializer):
    class Meta:
        model = UserLessonProgress
        fields = ["status", "completed_at", "best_score"]