# OTP-Based Password Reset Implementation

## ✅ Implemented - Complete Flow

### **Step-by-Step User Flow:**

```
1. User clicks "Forgot Password?"
   ↓
2. User enters email → Clicks "Send OTP"
   ↓
3. Backend generates 6-digit OTP → Sends email
   ↓
4. User sees "OTP sent!" message
   ↓
5. Frontend shows OTP input field
   ↓
6. User enters OTP from email → Clicks "Verify OTP"
   ↓
7. Backend verifies OTP
   ↓
8. Frontend shows password reset form
   ↓
9. User enters new password (2x) → Clicks "Reset Password"
   ↓
10. Backend validates OTP + Password → Updates password
   ↓
11. ✅ Success! User can now login with new password
```

---

## 📡 API Endpoints

### **1. Request OTP** (Step 1)

**Endpoint:** `POST /api/auth/forgot-password/`

**Request:**

```json
{
  "email": "user@example.com"
}
```

**Response:**

```json
{
  "message": "If an account exists with this email, an OTP has been sent.",
  "email": "user@example.com",
  "otp": "123456" // Only in development mode
}
```

**What Happens:**

- ✅ Generates random 6-digit OTP (e.g., `582914`)
- ✅ Stores OTP in `verification_token` field
- ✅ Stores timestamp in `last_activity` field
- ✅ Sends email with OTP
- ✅ OTP expires in **10 minutes**

---

### **2. Verify OTP** (Step 2 - Optional)

**Endpoint:** `POST /api/auth/verify-otp/`

**Request:**

```json
{
  "email": "user@example.com",
  "otp": "123456"
}
```

**Response - Success:**

```json
{
  "message": "OTP verified successfully",
  "email": "user@example.com"
}
```

**Response - Error:**

```json
{
  "error": "Invalid OTP. Please try again."
}
// OR
{
  "error": "OTP has expired. Please request a new one."
}
```

**What Happens:**

- ✅ Checks if OTP matches
- ✅ Checks if OTP expired (10 min limit)
- ✅ Returns success/error

---

### **3. Reset Password with OTP** (Step 3)

**Endpoint:** `POST /api/auth/password-reset-confirm/`

**Request:**

```json
{
  "email": "user@example.com",
  "otp": "123456",
  "new_password": "NewPassword123!",
  "confirm_password": "NewPassword123!"
}
```

**Response - Success:**

```json
{
  "message": "Password reset successfully. You can now log in."
}
```

**Response - Errors:**

```json
{
  "error": "Passwords do not match"
}
// OR
{
  "error": "Invalid OTP"
}
// OR
{
  "error": "OTP has expired. Please request a new one."
}
// OR
{
  "error": [
    "Password must be at least 8 characters.",
    "Password must include at least one uppercase letter."
  ]
}
```

**What Happens:**

- ✅ Verifies OTP again
- ✅ Checks OTP expiry
- ✅ Validates password strength (8+ chars, uppercase, digit, special char)
- ✅ Updates password with Argon2 hashing
- ✅ Clears OTP from database
- ✅ User can now login

---

## 📧 Email Format

**Subject:** Your GnyanSetu Password Reset OTP

**Body:**

```
Hello Virat Kohli,

You requested to reset your password for your GnyanSetu account.

Your One-Time Password (OTP) is:

    582914

This OTP will expire in 10 minutes.

If you didn't request this, please ignore this email and your password will remain unchanged.

Best regards,
GnyanSetu Team
```

---

## 🔒 Security Features

1. **6-Digit OTP**: Random number between 100000-999999
2. **10-Minute Expiry**: OTP expires after 10 minutes
3. **Single Use**: OTP is cleared after successful password reset
4. **No User Enumeration**: Always returns success message even if email doesn't exist
5. **Password Validation**: Enforces strong password rules
6. **Argon2 Hashing**: Most secure password hashing algorithm

---

## 🗄️ Database Storage

When OTP is generated:

```
User Record:
- verification_token = "582914"  (the OTP)
- last_activity = "2025-10-05 11:30:00"  (OTP creation time)
```

After password reset:

```
User Record:
- verification_token = NULL  (OTP cleared)
- password = "$argon2id$v=19$m=..."  (new hashed password)
```

---

## 🧪 Testing Flow (Development Mode)

### **Step 1: Request OTP**

```bash
curl -X POST http://localhost:8002/api/auth/forgot-password/ \
  -H "Content-Type: application/json" \
  -d '{"email": "virat@gmail.com"}'
```

**Check Django Terminal** - You'll see:

```
Your One-Time Password (OTP) is:

    582914

This OTP will expire in 10 minutes.
```

**Response includes OTP** (dev only):

```json
{
  "message": "If an account exists with this email, an OTP has been sent.",
  "email": "virat@gmail.com",
  "otp": "582914"
}
```

### **Step 2: Verify OTP (Optional)**

```bash
curl -X POST http://localhost:8002/api/auth/verify-otp/ \
  -H "Content-Type: application/json" \
  -d '{"email": "virat@gmail.com", "otp": "582914"}'
```

### **Step 3: Reset Password**

```bash
curl -X POST http://localhost:8002/api/auth/password-reset-confirm/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "virat@gmail.com",
    "otp": "582914",
    "new_password": "Virat2024!",
    "confirm_password": "Virat2024!"
  }'
```

---

## 🎨 Frontend Integration (To Do)

The frontend needs to be updated to support the new OTP flow:

### **Current State:**

- ✅ Has forgot password form
- ✅ Calls `/api/auth/forgot-password/`
- ❌ No OTP input screen
- ❌ No verify OTP step
- ❌ No password reset form with OTP

### **Updates Needed:**

1. **After user enters email:**

   - Show OTP input field (6 digits)
   - Add "Resend OTP" button
   - Add timer (10:00 countdown)

2. **After user enters OTP:**

   - Call `/api/auth/verify-otp/`
   - If valid, show password reset form
   - If invalid, show error

3. **Password reset form:**
   - Include OTP as hidden field
   - Two password fields
   - Submit to `/api/auth/password-reset-confirm/`

---

## ⏱️ OTP Expiry Logic

```python
# OTP is valid if:
current_time - otp_creation_time < 10 minutes

# Example:
OTP created: 11:30:00
Current time: 11:35:00
Difference: 5 minutes ✅ Valid

Current time: 11:41:00
Difference: 11 minutes ❌ Expired
```

---

## 📊 Comparison: Link vs OTP

| Feature                 | Link-Based                       | OTP-Based (New)        |
| ----------------------- | -------------------------------- | ---------------------- |
| **User Experience**     | Click link from email            | Enter 6-digit code     |
| **Security**            | Medium (link can be intercepted) | Higher (time-limited)  |
| **Expiry**              | 24 hours                         | 10 minutes             |
| **Mobile Friendly**     | Hard to click link               | Easy to copy/paste OTP |
| **Email Client**        | Needs clickable links            | Works with plain text  |
| **Reusability**         | One-time use                     | One-time use           |
| **Frontend Complexity** | Needs separate page              | Needs OTP input        |

---

## 🚀 Next Steps

1. ✅ **Backend Complete** - OTP generation, verification, password reset
2. ✅ **Email Sending** - OTP sent to email (console mode)
3. ⏳ **Frontend Updates Needed**:
   - Add OTP input screen
   - Add verify OTP step
   - Update password reset form to include OTP
   - Add "Resend OTP" functionality
   - Add countdown timer

---

## 🐛 Error Handling

| Error                 | Response                                                                       |
| --------------------- | ------------------------------------------------------------------------------ |
| Email not found       | `"If an account exists with this email, an OTP has been sent."` (don't reveal) |
| Invalid OTP           | `"Invalid OTP. Please try again."`                                             |
| Expired OTP           | `"OTP has expired. Please request a new one."`                                 |
| Passwords don't match | `"Passwords do not match"`                                                     |
| Weak password         | `"Password must be at least 8 characters."` (+ other rules)                    |
| Missing fields        | `"All fields are required"`                                                    |

---

## 🔄 Resend OTP Flow (To Implement)

User can request new OTP by:

1. Clicking "Resend OTP" button
2. Calling same endpoint: `/api/auth/forgot-password/`
3. New OTP generated
4. Old OTP becomes invalid
5. New OTP sent to email

---

## ✅ What's Working Now

1. ✅ User requests OTP → Backend sends 6-digit OTP
2. ✅ OTP stored in database with timestamp
3. ✅ OTP expires in 10 minutes
4. ✅ Verify OTP endpoint working
5. ✅ Reset password with OTP working
6. ✅ Password validation enforced
7. ✅ OTP cleared after successful reset

**Try it now!** Enter your email in the forgot password form and check your Django terminal for the OTP! 🎉
