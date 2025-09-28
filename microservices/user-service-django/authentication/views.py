from rest_framework import status, permissions, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import logout
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import transaction
import uuid
import logging

from .models import User, UserProfile, UserSession
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserRegistrationSerializer,
    UserSerializer,
    UserUpdateSerializer,
    UserProfileSerializer,
    PasswordChangeSerializer,
    UserSessionSerializer,
    EmailVerificationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
)

logger = logging.getLogger(__name__)


# Health Check
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def health_check(request):
    """
    Health check endpoint for service monitoring
    """
    return Response({
        'status': 'healthy',
        'service': 'GnyanSetu User Authentication Service',
        'version': '1.0.0',
        'timestamp': timezone.now()
    })


# Authentication Views
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT token obtain view with user session tracking
    """
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        # Log incoming request data for debugging
        logger.info(f"Login attempt - Data: {request.data}, Content-Type: {request.content_type}")
        
        try:
            response = super().post(request, *args, **kwargs)
            
            if response.status_code == 200:
                # Track user session
                user = User.objects.get(email=request.data.get('email'))
                self._create_user_session(request, user, response.data.get('access'))
                
                # Add user info to response
                response.data['user'] = {
                    'id': str(user.id),
                    'email': user.email,
                    'full_name': user.get_full_name(),
                    'is_verified': user.is_verified,
                    'learning_level': user.learning_level,
                }
                
                logger.info(f"User {user.email} logged in successfully")
            else:
                logger.warning(f"Login failed - Status: {response.status_code}, Data: {request.data}")
            
            return response
        except Exception as e:
            logger.error(f"Login error: {str(e)}, Request data: {request.data}")
            raise
    
    def _create_user_session(self, request, user, access_token):
        """Create user session record"""
        try:
            UserSession.objects.create(
                user=user,
                session_token=access_token[:50],  # Store partial token for identification
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                device_info={
                    'platform': request.META.get('HTTP_SEC_CH_UA_PLATFORM', ''),
                    'mobile': request.META.get('HTTP_SEC_CH_UA_MOBILE', ''),
                }
            )
        except Exception as e:
            logger.error(f"Failed to create user session: {e}")
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class UserRegistrationView(APIView):
    """
    User registration endpoint
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    user = serializer.save()
                    
                    # Generate verification token
                    verification_token = str(uuid.uuid4())
                    user.verification_token = verification_token
                    user.save()
                    
                    # Send verification email (in production)
                    if settings.EMAIL_BACKEND != 'django.core.mail.backends.console.EmailBackend':
                        self._send_verification_email(user, verification_token)
                    
                    # Generate JWT tokens
                    refresh = RefreshToken.for_user(user)
                    
                    logger.info(f"New user registered: {user.email}")
                    
                    return Response({
                        'message': 'User registered successfully',
                        'user': UserSerializer(user).data,
                        'tokens': {
                            'refresh': str(refresh),
                            'access': str(refresh.access_token),
                        },
                        'verification_required': True
                    }, status=status.HTTP_201_CREATED)
                    
            except Exception as e:
                logger.error(f"Registration failed: {e}")
                return Response({
                    'error': 'Registration failed. Please try again.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _send_verification_email(self, user, token):
        """Send email verification (placeholder)"""
        subject = 'Verify your GnyanSetu account'
        message = f'Click this link to verify your account: {settings.FRONTEND_URL}/verify-email?token={token}&email={user.email}'
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])


class LogoutView(APIView):
    """
    User logout endpoint
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            # Update user session
            UserSession.objects.filter(
                user=request.user,
                is_active=True
            ).update(
                is_active=False,
                logout_time=timezone.now()
            )
            
            logger.info(f"User {request.user.email} logged out")
            
            return Response({
                'message': 'Successfully logged out'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Logout failed: {e}")
            return Response({
                'error': 'Logout failed'
            }, status=status.HTTP_400_BAD_REQUEST)


# User Management Views
class UserProfileViewSet(ModelViewSet):
    """
    ViewSet for user profile management
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        serializer = UserUpdateSerializer(
            self.get_object(), 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            logger.info(f"User {request.user.email} updated profile")
            return Response(UserSerializer(self.get_object()).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileDetailView(generics.RetrieveUpdateAPIView):
    """
    Detailed user profile view
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


class PasswordChangeView(APIView):
    """
    Password change endpoint
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Password changed for user {request.user.email}")
            return Response({
                'message': 'Password changed successfully'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserSessionsView(generics.ListAPIView):
    """
    List user active sessions
    """
    serializer_class = UserSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserSession.objects.filter(
            user=self.request.user,
            is_active=True
        ).order_by('-login_time')


# Email Verification
class EmailVerificationView(APIView):
    """
    Email verification endpoint
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            user.is_verified = True
            user.verification_token = None
            user.save()
            
            logger.info(f"Email verified for user {user.email}")
            
            return Response({
                'message': 'Email verified successfully'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendVerificationEmailView(APIView):
    """
    Resend verification email
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        user = request.user
        
        if user.is_verified:
            return Response({
                'message': 'Email already verified'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate new verification token
        verification_token = str(uuid.uuid4())
        user.verification_token = verification_token
        user.save()
        
        # Send verification email (placeholder)
        logger.info(f"Verification email resent to {user.email}")
        
        return Response({
            'message': 'Verification email sent'
        }, status=status.HTTP_200_OK)


# Password Reset
class PasswordResetRequestView(APIView):
    """
    Password reset request endpoint
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)
            
            # Generate reset token
            reset_token = str(uuid.uuid4())
            user.verification_token = reset_token
            user.save()
            
            # Send reset email (placeholder)
            logger.info(f"Password reset requested for {email}")
            
            return Response({
                'message': 'Password reset email sent'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """
    Password reset confirmation endpoint
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            new_password = serializer.validated_data['new_password']
            
            user.set_password(new_password)
            user.verification_token = None
            user.save()
            
            logger.info(f"Password reset completed for {user.email}")
            
            return Response({
                'message': 'Password reset successfully'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Admin Views (for user management)
class AdminUserListView(generics.ListAPIView):
    """
    Admin view to list all users
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    def get_queryset(self):
        return User.objects.all().order_by('-date_joined')


class AdminUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Admin view for user management
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    queryset = User.objects.all()
    lookup_field = 'id'


# OAuth Placeholder Views
@api_view(['GET', 'POST'])
@permission_classes([permissions.AllowAny])
def google_oauth_placeholder(request):
    """
    Placeholder for Google OAuth integration
    """
    return Response({
        'error': 'Google OAuth not implemented yet',
        'message': 'Please use email/password authentication',
        'available_endpoints': {
            'login': '/api/auth/login/',
            'register': '/api/auth/register/',
            'signup': '/api/auth/signup/'
        }
    }, status=status.HTTP_501_NOT_IMPLEMENTED)


# Debug endpoint to check request data
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def debug_login_data(request):
    """
    Debug endpoint to see what data is being sent to login
    """
    return Response({
        'received_data': request.data,
        'content_type': request.content_type,
        'method': request.method,
        'headers': dict(request.headers),
    })
