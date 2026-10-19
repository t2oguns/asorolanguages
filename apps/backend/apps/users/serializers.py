from rest_framework import serializers
from .models import User, UserProfile, UserLearningStats


class UserProfileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="user.id", read_only=True)
    
    email = serializers.CharField(
        source="user.email",
        read_only=True,
    )

    class Meta:
        model = UserProfile
        fields = ["id","email", "display_name", "avatar_url"] 

