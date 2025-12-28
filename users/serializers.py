from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate

# Lấy User Model hiện tại của dự án (users.User)
User = get_user_model()

# 1. Serializer Đăng ký
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Mật khẩu nhập lại không khớp."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm') # Xóa trường confirm trước khi lưu
        # Dùng create_user để tự động mã hóa password (hash)
        user = User.objects.create_user(**validated_data)
        return user

# 2. Serializer Đăng nhập
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Tài khoản hoặc mật khẩu không đúng.")

# 3. Serializer Thông tin cá nhân (Profile)
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email'] # Thêm 'avatar' nếu model bạn có
        read_only_fields = ['id', 'username', 'email']