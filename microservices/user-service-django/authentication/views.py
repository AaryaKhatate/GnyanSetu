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
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

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
    Password reset request endpoint - Sends OTP to email
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            # Check if user exists (but don't reveal this to the client)
            try:
                user = User.objects.get(email=email)
                
                # Generate 6-digit OTP
                import random
                otp = str(random.randint(100000, 999999))
                
                # Store OTP in verification_token field with timestamp
                from django.utils import timezone
                user.verification_token = otp
                user.last_activity = timezone.now()  # Store OTP creation time
                user.save()
                
                # Send OTP email
                try:
                    send_mail(
                        subject='Your GnyanSetu Password Reset OTP',
                        message=f"""
Hello {user.full_name},

You requested to reset your password for your GnyanSetu account.

Your One-Time Password (OTP) is:

    {otp}

This OTP will expire in 10 minutes.

If you didn't request this, please ignore this email and your password will remain unchanged.

Best regards,
GnyanSetu Team
                        """,
                        from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@gnyansetu.com',
                        recipient_list=[email],
                        fail_silently=False,
                    )
                    logger.info(f"Password reset OTP sent to {email}")
                except Exception as e:
                    logger.error(f"Failed to send password reset OTP to {email}: {str(e)}")
                    # Still return success for security (don't reveal if email exists)
                
                # For development/testing: include OTP in response
                # TODO: Remove 'otp' field in production
                return Response({
                    'message': 'If an account exists with this email, an OTP has been sent.',
                    'email': email,  # Return email for next step
                    'otp': otp  # Include OTP in response for testing (remove in production)
                }, status=status.HTTP_200_OK)
                
            except User.DoesNotExist:
                # Email not found - return same generic message for security
                logger.info(f"Password reset requested for non-existent email: {email}")
                return Response({
                    'message': 'If an account exists with this email, an OTP has been sent.',
                    'email': email
                }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPView(APIView):
    """
    Verify OTP for password reset
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')
        
        if not email or not otp:
            return Response({
                'error': 'Email and OTP are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                'error': 'Invalid email or OTP'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if OTP matches
        if user.verification_token != otp:
            return Response({
                'error': 'Invalid OTP. Please try again.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if OTP is expired (10 minutes)
        from django.utils import timezone
        from datetime import timedelta
        
        if user.last_activity:
            otp_age = timezone.now() - user.last_activity
            if otp_age > timedelta(minutes=10):
                return Response({
                    'error': 'OTP has expired. Please request a new one.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"OTP verified successfully for {email}")
        
        return Response({
            'message': 'OTP verified successfully',
            'email': email
        }, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """
    Password reset confirmation endpoint - Reset password with OTP
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        
        if not all([email, otp, new_password, confirm_password]):
            return Response({
                'error': 'All fields are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if new_password != confirm_password:
            return Response({
                'error': 'Passwords do not match'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                'error': 'Invalid email or OTP'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify OTP again
        if user.verification_token != otp:
            return Response({
                'error': 'Invalid OTP'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check OTP expiry
        from django.utils import timezone
        from datetime import timedelta
        
        if user.last_activity:
            otp_age = timezone.now() - user.last_activity
            if otp_age > timedelta(minutes=10):
                return Response({
                    'error': 'OTP has expired. Please request a new one.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate password strength
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError
        
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response({
                'error': list(e.messages)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        user.set_password(new_password)
        user.verification_token = None  # Clear OTP
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


# OAuth Views
from allauth.socialaccount.models import SocialAccount
from rest_framework.decorators import api_view, permission_classes


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def google_oauth_callback(request):
    """
    Google OAuth callback handler
    Accepts Google ID token, verifies it, and creates/updates user
    
    Expected request body:
    {
        "token": "google_id_token_here",
        "client_id": "optional_client_id"
    }
    """
    try:
        token = request.data.get('token')
        
        if not token:
            return Response({
                'error': 'Token is required',
                'detail': 'Please provide Google ID token'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get Google Client ID from settings or request
        client_id = request.data.get('client_id') or getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', None)
        
        if not client_id:
            logger.error("Google OAuth Client ID not configured")
            return Response({
                'error': 'Google OAuth not configured',
                'detail': 'Please contact administrator'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Verify the Google ID token
        try:
            idinfo = id_token.verify_oauth2_token(
                token, 
                google_requests.Request(), 
                client_id
            )
            
            # Verify the token is for our app
            if idinfo['aud'] != client_id:
                raise ValueError('Token audience mismatch')
            
            # Extract user information from Google token
            google_id = idinfo['sub']
            email = idinfo.get('email')
            email_verified = idinfo.get('email_verified', False)
            full_name = idinfo.get('name', '')
            given_name = idinfo.get('given_name', '')
            family_name = idinfo.get('family_name', '')
            profile_picture = idinfo.get('picture', '')
            
            if not email:
                return Response({
                    'error': 'Email not provided by Google',
                    'detail': 'Please ensure email permission is granted'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            logger.info(f"Google OAuth: Verified token for {email}")
            
        except ValueError as e:
            logger.error(f"Google token verification failed: {e}")
            return Response({
                'error': 'Invalid Google token',
                'detail': str(e)
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Create or update user
        with transaction.atomic():
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email.split('@')[0] + '_' + str(uuid.uuid4())[:8],
                    'full_name': full_name,
                    'first_name': given_name,
                    'last_name': family_name,
                    'google_id': google_id,
                    'profile_picture': profile_picture,
                    'is_verified': email_verified,
                    'is_active': True,
                }
            )
            
            # Update existing user's Google info if they signed up with email first
            if not created:
                if not user.google_id:
                    user.google_id = google_id
                if not user.profile_picture and profile_picture:
                    user.profile_picture = profile_picture
                if not user.full_name and full_name:
                    user.full_name = full_name
                if email_verified and not user.is_verified:
                    user.is_verified = email_verified
                user.last_login = timezone.now()
                user.save()
                logger.info(f"Google OAuth: Updated existing user {email}")
            else:
                logger.info(f"Google OAuth: Created new user {email}")
            
            # Create or update user profile
            profile, _ = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'avatar': profile_picture,
                    'bio': f'Joined via Google Sign-In',
                }
            )
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Create user session
            UserSession.objects.create(
                user=user,
                session_token=str(refresh.access_token)[:50],
                ip_address=_get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                device_info={
                    'platform': request.META.get('HTTP_SEC_CH_UA_PLATFORM', ''),
                    'mobile': request.META.get('HTTP_SEC_CH_UA_MOBILE', ''),
                    'login_method': 'google_oauth'
                }
            )
            
            return Response({
                'message': 'Successfully authenticated with Google',
                'created': created,
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'username': user.username,
                    'full_name': user.full_name,
                    'profile_picture': user.profile_picture,
                    'is_verified': user.is_verified,
                    'google_id': user.google_id,
                },
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)
    
    except Exception as e:
        logger.error(f"Google OAuth error: {str(e)}", exc_info=True)
        return Response({
            'error': 'Authentication failed',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _get_client_ip(request):
    """Helper function to get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


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

