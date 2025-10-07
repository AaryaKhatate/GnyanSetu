"""
Custom password validators for GnyanSetu User Service
"""
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
import re


class MinimumLengthValidator:
    """
    Validates that the password is at least 8 characters long.
    """
    
    def __init__(self, min_length=8):
        self.min_length = min_length
    
    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                _("Password must be at least %(min_length)d characters."),
                code='password_too_short',
                params={'min_length': self.min_length},
            )
    
    def get_help_text(self):
        return _(
            "Your password must be at least %(min_length)d characters long."
            % {'min_length': self.min_length}
        )


class PasswordComplexityValidator:
    """
    Validates that the password contains at least one digit, one special character, and one uppercase letter.
    """
    
    def validate(self, password, user=None):
        errors = []
        
        # Check for at least one digit
        if not re.search(r'\d', password):
            errors.append(
                ValidationError(
                    _("Password must include at least one number."),
                    code='password_no_digit',
                )
            )
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', password):
            errors.append(
                ValidationError(
                    _("Password must include at least one uppercase letter."),
                    code='password_no_uppercase',
                )
            )
        
        # Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/;\'`~]', password):
            errors.append(
                ValidationError(
                    _("Password must include a special character (!@#$%^&* etc)."),
                    code='password_no_special',
                )
            )
        
        if errors:
            raise ValidationError(errors)
    
    def get_help_text(self):
        return _(
            "Your password must contain at least one number, one uppercase letter, and one special character."
        )
