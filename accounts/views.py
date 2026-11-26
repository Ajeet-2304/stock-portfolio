
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView
)

from .serializers import (
    RegisterSerializer,
    UserProfileSerializer, LoginSerializer
)


class RegisterAPIView(generics.CreateAPIView):

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class LoginAPIView(APIView):

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data['user']

            refresh = RefreshToken.for_user(user)

            return Response({
                "message": "Login successful",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email
                },
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            }, status=status.HTTP_200_OK)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class RefreshTokenAPIView(TokenRefreshView):

    permission_classes = [permissions.AllowAny]


class ProfileAPIView(generics.RetrieveUpdateAPIView):

    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):

        return self.request.user


class LogoutAPIView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):

        try:
            refresh_token = request.data.get("refresh")

            token = RefreshToken(refresh_token)

            token.blacklist()

            return Response({
                "message": "Successfully logged out."
            })

        except Exception:
            return Response({
                "error": "Invalid refresh token."
            }, status=400)