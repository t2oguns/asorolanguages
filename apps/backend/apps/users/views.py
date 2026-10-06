from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
# Create your views here.

class MeView(APIView):
    def get(self, request):
        u = request.user
        try:
            p = u.profile
            if p:
                return Response({"id": u.id, "email": u.email,
                                "display_name": p.display_name, "avatar_url": p.avatar_url})
        except Exception as e:
            return Response({"id": u.id, "email": u.email})