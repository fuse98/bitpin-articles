from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from users.serializer import LoginRequestSerializer


class Login(APIView):

    def post(self, request: Request):
        serializer = LoginRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'message': 'Must provide username and password'}, 400)

        user = authenticate(
            username=serializer.validated_data.get('username'),
            password=serializer.validated_data.get('password'),
        )
        if user is None:
            return Response({'message': 'Invalid credentials'}, 401)

        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})
