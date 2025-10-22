from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, UserProfile
# UserSession moved to MongoDB - see mongodb_manager.py


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom admin for User model
    """
    list_display = [
        'email', 'username', 'full_name', 'is_verified', 
        'learning_level', 'is_active', 'date_joined', 'last_activity'
    ]
    list_filter = [
        'is_verified', 'learning_level', 'is_active', 'is_staff',
        'preferred_language', 'date_joined'
    ]
    search_fields = ['email', 'username', 'full_name', 'phone_number']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Personal info', {
            'fields': (
                'email', 'full_name', 'first_name', 'last_name',
                'phone_number', 'date_of_birth', 'profile_picture', 'bio'
            )
        }),
        ('Educational preferences', {
            'fields': ('preferred_language', 'learning_level')
        }),
        ('Account status', {
            'fields': (
                'is_verified', 'verification_token', 'last_activity'
            )
        }),
        ('Permissions', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            ),
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'full_name', 'password1', 'password2',
                'preferred_language', 'learning_level'
            ),
        }),
    )
    
    readonly_fields = ['last_login', 'date_joined', 'created_at', 'updated_at', 'last_activity']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('profile')


class UserProfileInline(admin.TabularInline):
    """
    Inline admin for UserProfile
    """
    model = UserProfile
    extra = 0
    fields = [
        'education_level', 'institution', 'total_lessons_completed',
        'streak_days', 'email_notifications', 'public_profile'
    ]
    readonly_fields = ['total_lessons_completed', 'streak_days']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin for UserProfile model
    """
    list_display = [
        'user_email', 'education_level', 'institution',
        'total_lessons_completed', 'streak_days', 'last_lesson_date'
    ]
    list_filter = [
        'education_level', 'study_time_preference',
        'email_notifications', 'public_profile'
    ]
    search_fields = ['user__email', 'user__full_name', 'institution', 'field_of_study']
    ordering = ['-created_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Educational Background', {
            'fields': (
                'education_level', 'institution', 'field_of_study',
                'preferred_subjects', 'learning_goals'
            )
        }),
        ('Learning Preferences', {
            'fields': ('study_time_preference',)
        }),
        ('Statistics', {
            'fields': (
                'total_lessons_completed', 'total_study_time',
                'streak_days', 'last_lesson_date'
            )
        }),
        ('Settings', {
            'fields': (
                'email_notifications', 'push_notifications', 'public_profile'
            )
        }),
    )
    
    readonly_fields = [
        'total_lessons_completed', 'total_study_time',
        'streak_days', 'last_lesson_date'
    ]
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'


# UserSession Admin removed - sessions now stored in MongoDB
# To view sessions, query MongoDB directly or use the API endpoint /api/auth/sessions/


# Customize admin site
admin.site.site_header = "GnyanSetu User Administration"
admin.site.site_title = "GnyanSetu Admin"
admin.site.index_title = "User Management Dashboard"
