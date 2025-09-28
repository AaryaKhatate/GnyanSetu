from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'profile', views.UserProfileViewSet, basename='user-profile')

app_name = 'authentication'

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health_check'),
    
    # Authentication endpoints
    path('auth/login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/register/', views.UserRegistrationView.as_view(), name='register'),
    path('auth/signup/', views.UserRegistrationView.as_view(), name='signup'),  # Alias for frontend compatibility
    
    # Email verification
    path('auth/verify-email/', views.EmailVerificationView.as_view(), name='verify_email'),
    path('auth/resend-verification/', views.ResendVerificationEmailView.as_view(), name='resend_verification'),
    
    # Password reset
    path('auth/password-reset/', views.PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('auth/password-reset-confirm/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # User management
    path('auth/change-password/', views.PasswordChangeView.as_view(), name='change_password'),
    path('profile/details/', views.UserProfileDetailView.as_view(), name='profile_details'),
    path('sessions/', views.UserSessionsView.as_view(), name='user_sessions'),
    
    # Admin endpoints
    path('admin/users/', views.AdminUserListView.as_view(), name='admin_user_list'),
    path('admin/users/<uuid:id>/', views.AdminUserDetailView.as_view(), name='admin_user_detail'),
    
    # Include router URLs
    path('', include(router.urls)),
    
    # Debug endpoint
    path('debug/login/', views.debug_login_data, name='debug_login'),
]

# Additional compatibility URLs for frontend
compatibility_urlpatterns = [
    # Google OAuth compatibility (placeholder)
    path('accounts/google/login/', views.google_oauth_placeholder, name='google_oauth'),
]

urlpatterns += compatibility_urlpatterns