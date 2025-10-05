# Password Validation Rules - GnyanSetu User Service

## Current Password Constraints

Your Django User Authentication Service has **5 password validators** enabled:

### 1. **MinimumLengthValidator**

- **Requirement**: Password must be at least 8 characters long
- **Examples**:
  - ❌ `Pass12!` (only 7 characters)
  - ✅ `Password123!` (8+ characters)

### 2. **CommonPasswordValidator**

- **Requirement**: Password cannot be a commonly used password
- **Examples**:
  - ❌ `password` (too common)
  - ❌ `12345678` (too common)
  - ❌ `qwerty123` (too common)
  - ✅ `MySecurePass2024!` (unique)

### 3. **NumericPasswordValidator**

- **Requirement**: Password cannot be entirely numeric
- **Examples**:
  - ❌ `12345678` (all numbers)
  - ❌ `98765432` (all numbers)
  - ✅ `Pass12345!` (contains letters)

### 4. **UserAttributeSimilarityValidator**

- **Requirement**: Password cannot be too similar to username, email, or name
- **Examples**:
  - If username is `john_smith`:
    - ❌ `johnsmith123` (too similar)
    - ✅ `MySecurePass2024!` (different)

### 5. **PasswordComplexityValidator** ⭐ NEW

- **Requirement**: Password must contain at least one digit (0-9) AND one special character
- **Special characters allowed**: `!@#$%^&*(),.?":{}|<>_-+=[]\/;'` ` ~`
- **Examples**:
  - ❌ `Password` (no digit, no special char)
  - ❌ `Password123` (has digit, but no special char)
  - ❌ `Password!@#` (has special chars, but no digit)
  - ✅ `Password123!` (has both digit and special char)

## Why "12345678" Fails

The password `12345678` fails **THREE validators**:

1. ❌ **CommonPasswordValidator** - It's one of the most commonly used passwords
2. ❌ **NumericPasswordValidator** - It's entirely numeric
3. ❌ **PasswordComplexityValidator** - It has no special characters

## Recommended Password Examples

Here are some passwords that will pass all validators:

✅ `TestUser2024!`
✅ `MyPassword123@`
✅ `SecurePass@2024`
✅ `GnyanSetu123!`
✅ `Learning2024#`
✅ `Student@456`
✅ `Welcome2024$`

## Password Requirements Summary

A valid password must:

- ✅ Be at least **8 characters** long
- ✅ Contain **at least one digit** (0-9)
- ✅ Contain **at least one special character** (!@#$%^&\*() etc.)
- ✅ **Not be entirely numeric** (must contain at least one letter)
- ✅ **Not be too common** (avoid passwords like "password", "12345678", etc.)
- ✅ **Not be too similar** to your username, email, or name

## Configuration Location

Password validators are configured in:

```
d:\GnyanSetu\microservices\user-service-django\user_service\settings.py
```

Lines 99-119:

```python
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    {
        # Custom validator: Requires at least one digit and one special character
        'NAME': 'authentication.validators.PasswordComplexityValidator',
    },
]
```

Custom validator implementation:

```
d:\GnyanSetu\microservices\user-service-django\authentication\validators.py
```

## Frontend Changes Made

Updated `App.jsx` to display specific validation errors:

### Before:

- Error: "An error occurred" (generic)

### After:

- Error: "password: This password is too common. This password is entirely numeric. Password must contain at least one special character (!@#$%^&\*(),.?\":{}|<>\_-+=[]\\\/;'`~)."
- Error: "email: User with this email already exists."
- Error: "username: Username already taken."
- Error: "password: Password must contain at least one digit (0-9)."

Now users will see the **exact validation error** from the backend!

## Testing

Try signing up with these passwords to see the difference:

1. **Password: `12345678`**

   - Expected Error: "password: This password is too common. This password is entirely numeric. Password must contain at least one special character (!@#$%^&\*(),.?\":{}|<>\_-+=[]\\\/;'`~)."

2. **Password: `Password123`**

   - Expected Error: "password: Password must contain at least one special character (!@#$%^&\*(),.?\":{}|<>\_-+=[]\\\/;'`~)."

3. **Password: `Password!@#`**

   - Expected Error: "password: Password must contain at least one digit (0-9)."

4. **Password: `TestUser123!`**

   - Expected: Success ✅

5. **Password: `abc`**
   - Expected Error: "password: This password is too short. It must contain at least 8 characters."

## Disabling Validators (Development Only)

If you want to disable validators for development, edit `settings.py`:

```python
AUTH_PASSWORD_VALIDATORS = [
    # Commented out for development testing
    # {
    #     'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    # },
    # ... etc
]
```

⚠️ **Warning**: Never disable validators in production!
