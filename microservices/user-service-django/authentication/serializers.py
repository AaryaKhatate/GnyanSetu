from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import User, UserProfile, UserSession
import re
import logging

logger = logging.getLogger(__name__)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT token serializer with additional user information
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['user_id'] = str(user.id)
        token['email'] = user.email
        token['full_name'] = user.get_full_name()
        token['is_verified'] = user.is_verified
        token['learning_level'] = user.learning_level
        
        return token
    
    def validate(self, attrs):
        # Use email as username for authentication
        email = attrs.get('email') or attrs.get('username')
        password = attrs.get('password')
        
        if email and password:
            # Try to find user by email
            try:
                user = User.objects.get(email=email)
                if user.check_password(password):
                    # Update last activity
                    user.last_activity = timezone.now()
                    user.save(update_fields=['last_activity'])
                    
                    # Set the user in attrs for token generation
                    attrs['user'] = user
                    # Override username for JWT compatibility
                    attrs['username'] = user.username
                    return super().validate(attrs)
                else:
                    raise serializers.ValidationError('Invalid email or password.')
            except User.DoesNotExist:
                raise serializers.ValidationError('Invalid email or password.')
        
        return super().validate(attrs)


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    User registration serializer with validation
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    full_name = serializers.CharField(required=True, max_length=255)
    terms_accepted = serializers.BooleanField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'username', 'full_name', 'password', 'password_confirm',
            'phone_number', 'date_of_birth', 'preferred_language',
            'learning_level', 'terms_accepted'
        ]
        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': True},
        }
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return value
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already taken.")
        
        # Username validation
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError("Username can only contain letters, numbers, and underscores.")
        
        return value
    
    def validate_phone_number(self, value):
        if value and not re.match(r'^\+?1?\d{9,15}$', value):
            raise serializers.ValidationError("Invalid phone number format.")
        return value
    
    def validate_terms_accepted(self, value):
        if not value:
            raise serializers.ValidationError("You must accept the terms and conditions.")
        return value
    
    def validate(self, attrs):
        password = attrs.get('password')
        password_confirm = attrs.pop('password_confirm', None)
        
        logger.info(f"Validating password for user: {attrs.get('email')}")
        
        if password != password_confirm:
            raise serializers.ValidationError("Passwords do not match.")
        
        # Validate password strength with user context
        try:
            # Create a temporary user object for validation
            user = User(
                email=attrs.get('email'),
                username=attrs.get('username'),
                full_name=attrs.get('full_name', '')
            )
            logger.info(f"Calling validate_password for: {password}")
            validate_password(password, user=user)
            logger.info("Password validation passed!")
        except ValidationError as e:
            logger.error(f"Password validation failed: {e.messages}")
            raise serializers.ValidationError({"password": e.messages})
        
        attrs.pop('terms_accepted')  # Remove from attrs as it's not a model field
        return attrs
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        
        # Create user profile
        UserProfile.objects.create(user=user)
        
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
    User profile serializer for detailed profile management
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    is_verified = serializers.BooleanField(source='user.is_verified', read_only=True)
    date_joined = serializers.DateTimeField(source='user.date_joined', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'user_email', 'username', 'full_name', 'is_verified', 'date_joined',
            'education_level', 'institution', 'field_of_study',
            'preferred_subjects', 'learning_goals', 'study_time_preference',
            'total_lessons_completed', 'total_study_time', 'streak_days',
            'last_lesson_date', 'email_notifications', 'push_notifications',
            'public_profile', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'total_lessons_completed', 'total_study_time', 'streak_days',
            'last_lesson_date', 'created_at', 'updated_at'
        ]


class UserSerializer(serializers.ModelSerializer):
    """
    User serializer for general user information
    """
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'full_name', 'first_name', 'last_name',
            'phone_number', 'date_of_birth', 'profile_picture', 'bio',
            'is_verified', 'preferred_language', 'learning_level',
            'last_activity', 'date_joined', 'profile'
        ]
        read_only_fields = ['id', 'is_verified', 'date_joined']
    
    def validate_phone_number(self, value):
        if value and not re.match(r'^\+?1?\d{9,15}$', value):
            raise serializers.ValidationError("Invalid phone number format.")
        return value


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user information
    """
    class Meta:
        model = User
        fields = [
            'full_name', 'first_name', 'last_name', 'phone_number',
            'date_of_birth', 'profile_picture', 'bio', 'preferred_language',
            'learning_level'
        ]
    
    def validate_phone_number(self, value):
        if value and not re.match(r'^\+?1?\d{9,15}$', value):
            raise serializers.ValidationError("Invalid phone number format.")
        return value


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for changing user password
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    new_password_confirm = serializers.CharField(required=True)
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Incorrect old password.")
        return value
    
    def validate(self, attrs):
        new_password = attrs.get('new_password')
        new_password_confirm = attrs.get('new_password_confirm')
        
        if new_password != new_password_confirm:
            raise serializers.ValidationError("New passwords do not match.")
        
        # Validate password strength
        try:
            validate_password(new_password)
        except ValidationError as e:
            raise serializers.ValidationError({"new_password": e.messages})
        
        return attrs
    
    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class UserSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for user session information
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = UserSession
        fields = [
            'id', 'user_email', 'ip_address', 'user_agent', 'device_info',
            'is_active', 'login_time', 'logout_time', 'last_activity',
            'is_suspicious', 'failed_attempts'
        ]
        read_only_fields = [
            'id', 'user_email', 'login_time', 'logout_time', 'last_activity',
            'failed_attempts'
        ]


class EmailVerificationSerializer(serializers.Serializer):
    """
    Serializer for email verification
    """
    email = serializers.EmailField(required=True)
    token = serializers.CharField(required=True, max_length=255)
    
    def validate(self, attrs):
        email = attrs.get('email')
        token = attrs.get('token')
        
        try:
            user = User.objects.get(email=email, verification_token=token)
            if user.is_verified:
                raise serializers.ValidationError("Email already verified.")
            attrs['user'] = user
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid verification token.")
        
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for password reset request
    """
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user found with this email address.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for password reset confirmation
    """
    email = serializers.EmailField(required=True)
    token = serializers.CharField(required=True, max_length=255)
    new_password = serializers.CharField(required=True, min_length=8)
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        token = attrs.get('token')
        new_password = attrs.get('new_password')
        new_password_confirm = attrs.get('new_password_confirm')
        
        if new_password != new_password_confirm:
            raise serializers.ValidationError("Passwords do not match.")
        
        # Validate password strength
        try:
            validate_password(new_password)
        except ValidationError as e:
            raise serializers.ValidationError({"new_password": e.messages})
        
        # Verify reset token (simplified - in production use proper token system)
        try:
            user = User.objects.get(email=email, verification_token=token)
            attrs['user'] = user
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid reset token.")
        
        return attrs