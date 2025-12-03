#user serialization for logging and registering
from hmac import new
from os import read, write
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
import logging  
_logger = logging.getLogger(__name__)
User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        help_text='INPUT STRONG PASSWORD!'
    )
    
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text='CONFIRM YOUR PASSWORD!'
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm')
        extra_kwargs = {
            'username': {'help_text': 'USERNAME REQUIRED!'},
        }
    
    def validate_username(self,username):
        username_exists = User.objects.filter(username__iexact= username).exists()
        if username_exists:
            raise serializers.ValidationError("USERNAME ALREADY EXISTS!")
        return username.lower()
    
    def validate(self, attrs):
        is_incorrect_password = attrs['password'] != attrs['password_confirm']
        if is_incorrect_password:
            raise serializers.ValidationError({"password_confirm": "PASSWORDS DO NOT MATCH!"})
        return attrs
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'date_joined', 'last_login')
        

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text='ENTER YOUR CURRENT PASSWORD!'
    )
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        help_text='ENTER YOUR NEW PASSWORD!'
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text='CONFIRM YOUR NEW PASSWORD!'
    )
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                "new_password_confirm": "New password fields didn't match."
            })
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user. check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value