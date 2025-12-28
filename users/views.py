from django.contrib.auth import login, logout
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserRegistrationSerializer, LoginSerializer, UserProfileSerializer

# 1. API ĐĂNG KÝ
class RegisterView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Tùy chọn: Auto login sau khi đăng ký
            login(request, user)
            return Response({
                "message": "Đăng ký thành công",
                "user": UserProfileSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 2. API ĐĂNG NHẬP
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            # Quan trọng: Lệnh này tạo session cookie cho browser
            login(request, user)
            return Response({
                "message": "Đăng nhập thành công",
                "user": UserProfileSerializer(user).data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 3. API ĐĂNG XUẤT
class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response({"message": "Đăng xuất thành công"}, status=status.HTTP_200_OK)

# 4. API HỒ SƠ (Xem & Cập nhật Avatar)
class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user