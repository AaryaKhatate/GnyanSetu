# Google OAuth Setup Guide for GnyanSetu

## Overview
This guide will help you set up Google OAuth for signup and login functionality.

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your Google account
3. Click on the project dropdown at the top and click "New Project"
4. Enter project name: `GnyanSetu` (or your preferred name)
5. Click "Create"

## Step 2: Enable Google+ API

1. In the Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for "Google+ API"
3. Click on it and click "Enable"

## Step 3: Configure OAuth Consent Screen

1. Go to "APIs & Services" > "OAuth consent screen"
2. Select "External" user type (unless you have a Google Workspace)
3. Click "Create"
4. Fill in the required information:
   - **App name**: GnyanSetu
   - **User support email**: Your email
   - **Developer contact information**: Your email
5. Click "Save and Continue"
6. On the "Scopes" page, click "Add or Remove Scopes"
7. Add these scopes:
   - `userinfo.email`
   - `userinfo.profile`
8. Click "Save and Continue"
9. On "Test users" page, you can add test users or skip for now
10. Click "Save and Continue"

## Step 4: Create OAuth Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Select "Web application"
4. Enter name: `GnyanSetu Web Client`
5. Add **Authorized JavaScript origins**:
   ```
   http://localhost:3000
   http://localhost:3001
   ```
6. Add **Authorized redirect URIs**:
   ```
   http://localhost:3000
   http://localhost:3001
   http://localhost:8002/accounts/google/login/callback/
   ```
7. Click "Create"
8. **IMPORTANT**: Copy the Client ID and Client Secret that appear

## Step 5: Configure Environment Variables

1. Create or edit `.env` file in `d:\GnyanSetu\microservices\user-service-django\`
2. Add these lines:
   ```env
   GOOGLE_CLIENT_ID=your_client_id_here
   GOOGLE_CLIENT_SECRET=your_client_secret_here
   LOGIN_REDIRECT_URL=http://localhost:3001/dashboard
   LOGOUT_REDIRECT_URL=http://localhost:3000
   ```
3. Replace `your_client_id_here` and `your_client_secret_here` with the actual values from Step 4

## Step 6: Install Required Packages

Run this command in PowerShell:
```powershell
cd d:\GnyanSetu\microservices\user-service-django
pip install google-auth==2.23.0 google-auth-oauthlib==1.1.0 google-auth-httplib2==0.1.1
```

## Step 7: Run Django Migrations

```powershell
python manage.py migrate
```

## Step 8: Restart Django Server

```powershell
# Stop the current server (Ctrl+C)
# Then restart:
python manage.py runserver 8002
```

## Step 9: Frontend Integration

### Add Google Sign-In Button to React

You need to install the Google OAuth library in your React frontend:

```bash
cd d:\GnyanSetu\virtual_teacher_project\UI
npm install @react-oauth/google
```

### Update App.jsx

Add the Google OAuth provider and button. Here's example code:

```javascript
import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google';

// Wrap your app with GoogleOAuthProvider
function App() {
  return (
    <GoogleOAuthProvider clientId="YOUR_GOOGLE_CLIENT_ID">
      {/* Your existing app components */}
    </GoogleOAuthProvider>
  );
}

// In your signup/login form component:
const handleGoogleSuccess = async (credentialResponse) => {
  try {
    const response = await fetch('http://localhost:8002/api/v1/auth/google/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        access_token: credentialResponse.credential
      })
    });
    
    const data = await response.json();
    
    if (response.ok) {
      // Save tokens
      localStorage.setItem('access_token', data.tokens.access);
      localStorage.setItem('refresh_token', data.tokens.refresh);
      
      // Redirect to dashboard
      window.location.href = 'http://localhost:3001/dashboard';
    } else {
      console.error('Google login failed:', data);
    }
  } catch (error) {
    console.error('Error during Google login:', error);
  }
};

// Add this button in your form:
<GoogleLogin
  onSuccess={handleGoogleSuccess}
  onError={() => console.log('Login Failed')}
  text="signup_with"
  shape="rectangular"
  theme="outline"
  size="large"
/>
```

## API Endpoints

### Google OAuth Callback
- **URL**: `http://localhost:8002/api/v1/auth/google/`
- **Method**: POST
- **Request Body**:
  ```json
  {
    "access_token": "google_access_token_here"
  }
  ```
- **Success Response** (200 OK):
  ```json
  {
    "message": "Authentication successful",
    "user": {
      "id": "user_uuid",
      "email": "user@gmail.com",
      "full_name": "User Name",
      "username": "username"
    },
    "tokens": {
      "access": "jwt_access_token",
      "refresh": "jwt_refresh_token"
    },
    "created": true
  }
  ```
- **Error Response** (400/401/500):
  ```json
  {
    "error": "Error message",
    "detail": "Detailed error description"
  }
  ```

## Testing

1. Make sure your Django server is running on port 8002
2. Make sure your React frontend is running on port 3000
3. Click the "Sign in with Google" button
4. Select a Google account
5. You should be redirected to the dashboard with JWT tokens stored

## Troubleshooting

### Error: "redirect_uri_mismatch"
- Make sure you added `http://localhost:3000` and `http://localhost:8002/accounts/google/login/callback/` to Authorized redirect URIs in Google Cloud Console

### Error: "invalid_client"
- Check that your `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env` are correct

### Error: "No access token provided"
- Check that the frontend is sending `access_token` in the request body
- Check the browser console for errors

### User created but can't login
- Check if the user's `email_verified` field is set to `True`
- Check if `is_active` is `True`

## Security Notes

1. **Never commit `.env` file to git** - Add it to `.gitignore`
2. **Use HTTPS in production** - Update redirect URIs to use `https://`
3. **Rotate secrets regularly** - Change Client Secret periodically
4. **Verify tokens** - The backend verifies tokens with Google before creating sessions

## What Happens During Google OAuth?

1. User clicks "Sign in with Google" on frontend
2. Google login popup appears
3. User selects Google account and grants permissions
4. Google returns an access token to the frontend
5. Frontend sends this token to our backend (`/api/v1/auth/google/`)
6. Backend verifies the token with Google
7. Backend extracts user info (email, name, picture)
8. Backend checks if user exists:
   - If yes: Login the existing user
   - If no: Create a new user account
9. Backend generates JWT tokens
10. Backend returns JWT tokens to frontend
11. Frontend stores tokens and redirects to dashboard

## Next Steps

After setting up Google OAuth:
- [ ] Create Google Cloud project and OAuth credentials
- [ ] Add credentials to `.env` file
- [ ] Install required packages
- [ ] Run migrations
- [ ] Restart Django server
- [ ] Install `@react-oauth/google` in React frontend
- [ ] Add Google login button to frontend
- [ ] Test the complete flow
