from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = UserProfile
        fields = ["user", "display_name", "avatar_url"] 


class MeSerializer(serializers.ModelSerializer):
    is_superuser = serializers.BooleanField(read_only=True)
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "is_superuser", "profile"]

    def get_profile(self, obj):
        try:
            profile = obj.profile
        except UserProfile.DoesNotExist:
            return None

        return UserProfileSerializer(profile).data
