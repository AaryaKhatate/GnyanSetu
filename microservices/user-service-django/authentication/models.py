from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import EmailValidator, RegexValidator
from django.utils import timezone
import uuid

class User(AbstractUser):
    """
    Extended User model with additional fields for GnyanSetu platform
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator()],
        help_text="Required. Enter a valid email address."
    )
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True, null=True)
    
    # Profile fields
    full_name = models.CharField(max_length=255, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_picture = models.URLField(blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    
    # Google OAuth fields
    google_id = models.CharField(max_length=255, blank=True, null=True, unique=True, 
                                  help_text="Google account ID for OAuth authentication")
    
    # Account status
    is_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=255, blank=True, null=True)
    last_activity = models.DateTimeField(default=timezone.now)
    
    # Educational preferences
    preferred_language = models.CharField(max_length=10, default='en')
    learning_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
        ],
        default='beginner'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Use email as username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'full_name']
    
    class Meta:
        db_table = 'auth_user_extended'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.email} ({self.full_name})"
    
    def get_full_name(self):
        return self.full_name or f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        return self.first_name or self.username


class UserProfile(models.Model):
    """
    Extended profile information for users
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Educational background
    education_level = models.CharField(
        max_length=50,
        choices=[
            ('primary', 'Primary School'),
            ('secondary', 'Secondary School'),
            ('undergraduate', 'Undergraduate'),
            ('graduate', 'Graduate'),
            ('postgraduate', 'Postgraduate'),
        ],
        blank=True
    )
    institution = models.CharField(max_length=255, blank=True)
    field_of_study = models.CharField(max_length=255, blank=True)
    
    # Learning preferences
    preferred_subjects = models.JSONField(default=list, blank=True)
    learning_goals = models.TextField(blank=True)
    study_time_preference = models.CharField(
        max_length=20,
        choices=[
            ('morning', 'Morning'),
            ('afternoon', 'Afternoon'),
            ('evening', 'Evening'),
            ('night', 'Night'),
        ],
        blank=True
    )
    
    # Statistics
    total_lessons_completed = models.PositiveIntegerField(default=0)
    total_study_time = models.PositiveIntegerField(default=0)  # in minutes
    streak_days = models.PositiveIntegerField(default=0)
    last_lesson_date = models.DateTimeField(blank=True, null=True)
    
    # Settings
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    public_profile = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"Profile for {self.user.email}"




# UserSession model moved to MongoDB - see mongodb_manager.py
# Sessions are now stored in MongoDB collection 'user_sessions'
# in database 'gnyansetu_users_django'
# This eliminates UNIQUE constraint issues with SQLite

