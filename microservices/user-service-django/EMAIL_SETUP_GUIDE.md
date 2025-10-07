# Email Setup Guide - Send Real Emails via Gmail

## 📧 Current Status

- ✅ Settings configured for Gmail SMTP
- ⏳ Need to add your Gmail credentials to `.env` file

---

## 🔧 Setup Steps

### Step 1: Enable Gmail App Password

You **cannot** use your regular Gmail password for SMTP. You need to create an **App Password**.

#### A. Enable 2-Factor Authentication (if not already enabled)

1. Go to your Google Account: https://myaccount.google.com/
2. Click **Security** (left sidebar)
3. Under "Signing in to Google", click **2-Step Verification**
4. Follow the steps to enable it

#### B. Generate App Password

1. Go to: https://myaccount.google.com/apppasswords
   - Or Google Account → Security → 2-Step Verification → App passwords
2. Select app: **Mail**
3. Select device: **Other (Custom name)**
4. Enter name: `GnyanSetu Django`
5. Click **Generate**
6. **Copy the 16-character password** (e.g., `abcd efgh ijkl mnop`)

---

### Step 2: Update `.env` File

Open `d:\GnyanSetu\microservices\user-service-django\.env` and update:

```properties
# Email Configuration (Gmail SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-actual-email@gmail.com
EMAIL_HOST_PASSWORD=abcd efgh ijkl mnop
DEFAULT_FROM_EMAIL=GnyanSetu <your-actual-email@gmail.com>
```

**Replace:**

- `your-actual-email@gmail.com` → Your Gmail address
- `abcd efgh ijkl mnop` → The 16-character App Password (without spaces)

**Example:**

```properties
EMAIL_HOST_USER=gnyansetu@gmail.com
EMAIL_HOST_PASSWORD=abcdefghijklmnop
DEFAULT_FROM_EMAIL=GnyanSetu <gnyansetu@gmail.com>
```

---

### Step 3: Restart Django Server

```powershell
# Stop the server (Ctrl+C)
# Then restart:
cd d:\GnyanSetu\microservices\user-service-django
python manage.py runserver 8002
```

---

## ✅ Test Email Sending

### Test Forgot Password Flow:

1. Go to http://localhost:3000
2. Click "Forgot Password"
3. Enter a registered email address
4. Click "Send OTP"
5. **Check your Gmail inbox** for the OTP email

### Expected Email:

```
Subject: Your GnyanSetu Password Reset OTP
From: GnyanSetu <your-email@gmail.com>

Hello [User Name],

You requested to reset your password for your GnyanSetu account.

Your One-Time Password (OTP) is:

    123456

This OTP will expire in 10 minutes.

If you didn't request this, please ignore this email and your password will remain unchanged.

Best regards,
GnyanSetu Team
```

---

## 🔄 Switch Between Console and Real Emails

### To Print to Terminal (Development):

```properties
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### To Send Real Emails (Production):

```properties
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
```

Just change the `EMAIL_BACKEND` in `.env` and restart Django.

---

## 🚨 Troubleshooting

### Error: "SMTPAuthenticationError: Username and Password not accepted"

- ✅ Make sure you're using **App Password**, not your regular Gmail password
- ✅ Remove spaces from the App Password (e.g., `abcd efgh ijkl mnop` → `abcdefghijklmnop`)
- ✅ Enable 2-Factor Authentication on your Google account

### Error: "SMTPException: STARTTLS extension not supported"

- ✅ Make sure `EMAIL_USE_TLS=True` in `.env`
- ✅ Make sure `EMAIL_PORT=587` (not 465 or 25)

### Email sent but not received:

- ✅ Check your Spam/Junk folder
- ✅ Check the Django terminal logs for "Email sent successfully"
- ✅ Verify the recipient email is correct

### Gmail blocks the email:

- ✅ Go to https://myaccount.google.com/lesssecureapps and enable it (if available)
- ✅ Or use App Password (recommended)

---

## 🔐 Security Notes

1. **Never commit `.env` to git** - It's already in `.gitignore`
2. **Use App Passwords** - More secure than your main password
3. **Rotate passwords** - Change App Password periodically
4. **Monitor usage** - Check Google Account activity for suspicious logins

---

## 📊 Email Sending Limits

**Gmail Free Account:**

- **500 emails/day** (or 2000 if Google Workspace)
- **500 recipients/email**

For production with high volume:

- Consider **SendGrid** (100 emails/day free)
- Or **Amazon SES** (62,000 emails/month free)
- Or **Mailgun** (5,000 emails/month free)

---

## ✨ Done!

Once you update `.env` with your Gmail credentials and restart Django, all emails (OTP, password reset, etc.) will be sent to real email addresses! 🎉

**Quick Test Command:**

```python
# Django shell test
python manage.py shell

from django.core.mail import send_mail
send_mail(
    'Test Email',
    'This is a test email from GnyanSetu!',
    'gnyansetu@gmail.com',
    ['your-email@gmail.com'],
    fail_silently=False,
)
```

If this works, your email setup is complete! ✅
