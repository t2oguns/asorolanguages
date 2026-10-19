from django.urls import reverse
from rest_framework import status
from apps.courses.models import Unit
from apps.courses.serializers import UnitSerializer

def test_unit_list(db, auth_client):
    Unit.objects.create(title="Unit 1")
    Unit.objects.create(title="Unit 2")

    url = reverse("unit-list")
    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data == UnitSerializer(
        Unit.objects.all(), many=True
    ).data
    assert len(response.data) == 2

def test_lesson_not_found(auth_client):
    url = reverse("get-lesson", kwargs={"code": "INVALID"})
    response = auth_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND