from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response

from users.serializers import LoginRequestSerializer, UserCreateSerializer


class LoginView(APIView):

    def post(self, request: Request):
        serializer = LoginRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            username=serializer.validated_data.get('username'),
            password=serializer.validated_data.get('password'),
        )
        if user is None:
            raise AuthenticationFailed('Invalid credentials')

        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key}, status=status.HTTP_200_OK)


class RegisterView(APIView):

    def post(self, request: Request):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "User created successfully",
                "user": {
                    "username": user.username,
                    "email": user.email,
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
