from django.core.exceptions import ValidationError as ModelValidationError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response

from apps.courses.models import Lesson, PUBLISH_STATUS
from apps.exercises.lessons import submission_receipt, lesson_payload, deliver_lesson, submit_lesson
from apps.exercises.models import LessonAttempt
from apps.exercises.serializers import (
    LessonSessionStartSerializer, LessonBatchSubmitSerializer,
    LessonSessionPayloadSerializer, SubmissionReceiptSerializer,
)


def run_lesson_service(function, **kwargs):
    try:
        return function(**kwargs)
    except ModelValidationError as error:
        raise serializers.ValidationError(error.messages)


class PublishedLessonMixin:
    permission_classes = [permissions.IsAuthenticated]
    queryset = Lesson.objects.filter(publication_status=PUBLISH_STATUS.PUBLISHED)
    lookup_field = "code"
    lookup_url_kwarg = "code"


class LessonSessionStartView(PublishedLessonMixin, generics.GenericAPIView):
    serializer_class = LessonSessionStartSerializer

    @extend_schema(responses={201: LessonSessionPayloadSerializer})
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = run_lesson_service(deliver_lesson, user=request.user, lesson=self.get_object(), **serializer.validated_data)
        response = Response(lesson_payload(session), status=status.HTTP_201_CREATED)
        response["Cache-Control"] = "private, no-store"
        return response


class LessonSessionSubmitView(PublishedLessonMixin, generics.GenericAPIView):
    queryset = Lesson.objects.all()  # Allow completion against already delivered content.
    http_method_names = ["post", "options"]
    serializer_class = LessonBatchSubmitSerializer

    def session(self):
        return get_object_or_404(LessonAttempt, pk=self.kwargs["session_id"], user=self.request.user, lesson=self.get_object())

    @extend_schema(responses=SubmissionReceiptSerializer)
    def post(self, request, *args, **kwargs):
        session = self.session()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = run_lesson_service(submit_lesson, user=request.user, session_id=session.pk, **serializer.validated_data)
        return Response(submission_receipt(result))
