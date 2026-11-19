from django.contrib.auth import authenticate
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer, RegisterSerializer


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=RegisterSerializer, responses={201: OpenApiTypes.OBJECT})
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # create token right away so user doesnt need to login again
        token = Token.objects.create(user=user)

        return Response({
            'message': 'User registered successfully',
            'user': {'id': user.id, 'username': user.username, 'email': user.email},
            'token': token.key,
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=LoginSerializer, responses={200: OpenApiTypes.OBJECT})
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password'],
        )
        if user is None:
            return Response({'error': 'Invalid username or password'}, status=status.HTTP_401_UNAUTHORIZED)

        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'message': 'Login successful',
            'token': token.key,
            'user': {'id': user.id, 'username': user.username, 'email': user.email},
        })


class LogoutView(APIView):

    @extend_schema(request=None, responses={200: OpenApiTypes.OBJECT})
    def post(self, request):
        # deleting the token means it cant be used anymore
        request.user.auth_token.delete()
        return Response({'message': 'Logged out successfully'})
