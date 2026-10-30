from django.urls import reverse
from rest_framework import status
from apps.courses.models import Unit
from apps.courses.serializers import UnitSerializer
from tests.factories import make_unit

def test_unit_list(lesson, auth_client):

    url = reverse("apps.courses:unit-list")
    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data == UnitSerializer(
        Unit.objects.all(), many=True
    ).data
    assert len(response.data) == 1

def test_lesson_not_found(auth_client):
    url = reverse("apps.courses:get-lesson", kwargs={"code": "INVALID1"})
    response = auth_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND