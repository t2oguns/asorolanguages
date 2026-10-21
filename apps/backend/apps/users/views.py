from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import MeSerializer

# Create your views here.

class MeView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MeSerializer

    def get(self, request):
        serializer = MeSerializer(request.user)
        return Response(serializer.data)