from email.policy import HTTP
from django.shortcuts import render
import logging

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    RegisterSerializer,
    UserSerializer,
    ChangePasswordSerializer
)

_logger = logging.getLogger(__name__)
User = get_user_model()
# Create your views here.


class RegisterUser(CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        _logger.debug("Registering a new user")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        
        _logger.info(f"New user registered: {user.username}")
        return Response(
            {
                "id": user.id,
                "username": user.username,
                "message": "USER REGISTERED SUCCESSFULLY!"
            },
            status = status.HTTP_201_CREATED
        )

class UserProfile(APIView):
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        _logger.debug(f"Fetching profile for user: {request.user.username}")
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        _logger. info(f"PASSWORD CHANGE STARTED: {request.user. username}")
        
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        request.user.set_password(serializer.validated_data['new_password'])
        request.user. save()
        
        _logger. info(f"PASSWORD CHANGED SUCCESSFULLY: {request.user.username}")
        
        return Response(
            {"message": "CHANGED SUCCESFULLY PASSWORD"},
            status=status.HTTP_200_OK
        )