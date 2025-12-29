from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()

class MeSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "avatar",
            "avatar_url",
        ]
        read_only_fields = ["id", "username"]

    def get_avatar_url(self, obj):
        request = self.context.get("request")
        if not obj.avatar:
            return None
        url = obj.avatar.url
        return request.build_absolute_uri(url) if request else url
