# Forgot Password Implementation

## ✅ What's Been Implemented

### Backend (Django)

1. **Endpoint**: `/api/auth/forgot-password/` (alias for `/api/auth/password-reset/`)
2. **Method**: POST
3. **Request Body**:
   ```json
   {
     "email": "user@example.com"
   }
   ```

### How It Works

#### Step 1: User Requests Password Reset

1. User enters their email in the "Forgot Password" form
2. Frontend sends POST request to `/api/auth/forgot-password/`
3. Backend validates the email

#### Step 2: Backend Sends Reset Email

1. Backend generates a unique reset token (UUID)
2. Saves the token to user's `verification_token` field
3. Sends email with reset link: `http://localhost:3000/reset-password?token={token}&email={email}`
4. Returns success message (even if email doesn't exist - security best practice)

#### Step 3: User Clicks Reset Link

1. User receives email and clicks the reset link
2. Frontend shows password reset form
3. User enters new password

#### Step 4: Password Reset Confirmation

1. Frontend sends POST request to `/api/auth/password-reset-confirm/`
2. Backend validates token and updates password

---

## 📧 Email Configuration

Currently using **Console Backend** - emails are printed to the Django terminal instead of being sent.

**To see the email in the terminal:**

1. Look at your Django server terminal
2. You'll see the email content printed there
3. Copy the reset link from the terminal

**Current Settings** (`settings.py`):

```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

**To send real emails (Gmail example):**
Add to `.env`:

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

Update `settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@gnyansetu.com')
```

---

## 🧪 Testing the Flow

### Test 1: Request Password Reset

```bash
curl -X POST http://localhost:8002/api/auth/forgot-password/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

**Expected Response:**

```json
{
  "message": "If an account exists with this email, a password reset link has been sent.",
  "reset_link": "http://localhost:3000/reset-password?token=abc123&email=test@example.com"
}
```

**Check Django Terminal** - you'll see the email content printed.

### Test 2: Reset Password

```bash
curl -X POST http://localhost:8002/api/auth/password-reset-confirm/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "token": "abc123",
    "new_password": "NewPassword123!",
    "confirm_password": "NewPassword123!"
  }'
```

**Expected Response:**

```json
{
  "message": "Password reset successfully"
}
```

---

## 📝 API Endpoints Summary

### 1. Forgot Password Request

- **URL**: `POST /api/auth/forgot-password/`
- **Body**: `{ "email": "user@email.com" }`
- **Response**: `{ "message": "...", "reset_link": "..." }`

### 2. Password Reset Confirmation

- **URL**: `POST /api/auth/password-reset-confirm/`
- **Body**:
  ```json
  {
    "email": "user@email.com",
    "token": "reset-token",
    "new_password": "NewPass123!",
    "confirm_password": "NewPass123!"
  }
  ```
- **Response**: `{ "message": "Password reset successfully" }`

---

## 🎨 Frontend Integration

The frontend (`App.jsx`) already has:

1. ✅ Forgot password form
2. ✅ API call to `/api/auth/forgot-password/`
3. ✅ Success/error handling

**What's Missing:**

- Password reset page (the page user lands on after clicking email link)
- Form to enter new password
- Token validation

---

## 🔒 Security Features

1. **Token-based reset**: Uses UUID tokens stored in database
2. **No user enumeration**: Always returns success message even if email doesn't exist
3. **Password validation**: Enforces password strength rules
4. **Token expiry**: Tokens can be manually expired (add expiry logic if needed)

---

## 🚀 Next Steps

1. ✅ Backend endpoint working
2. ✅ Email sending configured (console mode)
3. ⏳ **Need to create**: Password reset page in frontend

   - Route: `/reset-password`
   - Parse token and email from URL
   - Show new password form
   - Submit to `/api/auth/password-reset-confirm/`

4. 🔧 **Optional**: Configure real email sending (Gmail/SendGrid)

---

## 📊 Database Changes

When user requests password reset:

- `verification_token` field is updated with UUID
- Token is used to verify the reset request
- Token is cleared after successful password reset

---

## 🐛 Troubleshooting

### Email not showing in terminal

- Check that Django server is running
- Email will be printed in the Django terminal, not the browser

### "Email not found" error

- Check that user exists in database
- Use DB Browser to verify email

### Reset link doesn't work

- Frontend needs a route for `/reset-password`
- Currently, clicking the link will show 404

### Password reset fails

- Check that token matches in database
- Check password meets validation requirements
