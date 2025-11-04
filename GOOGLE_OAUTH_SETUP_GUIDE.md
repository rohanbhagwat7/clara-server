# Google OAuth Setup Guide for Clara

## Overview

Google OAuth 2.0 allows users to sign in to Clara using their existing Google accounts. This provides:

✅ **Secure Authentication** - No need to manage passwords
✅ **Quick Onboarding** - Users can log in with one tap
✅ **Trust** - Users trust Google's security
✅ **Profile Data** - Automatically get name, email, profile picture

---

## How Google OAuth Works

### The OAuth 2.0 Flow

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│             │         │              │         │             │
│  Clara App  │────1───>│    Google    │────2───>│    User     │
│  (Mobile)   │<───4────│    OAuth     │<───3────│  (Browser)  │
│             │         │              │         │             │
└─────────────┘         └──────────────┘         └─────────────┘
       │                                                │
       │                                                │
       5. Send ID Token                                 │
       │                                                │
       v                                                │
┌─────────────┐         ┌──────────────┐               │
│             │         │              │               │
│Clara Server │────6───>│Google Token  │               │
│  (Backend)  │<───7────│ Verification │               │
│             │         │              │               │
└─────────────┘         └──────────────┘               │
       │                                                │
       │                                                │
       8. Return JWT Token                              │
       v                                                │
┌─────────────┐                                         │
│             │                                         │
│  Logged In  │<────────────────────────────────────────┘
│             │
└─────────────┘
```

**Step-by-Step:**

1. **User taps "Sign in with Google"** in Clara app
2. **Google OAuth screen opens** in browser/web view
3. **User authorizes** Clara to access their Google profile
4. **Google returns ID Token** to Clara app
5. **Clara app sends ID Token** to Clara server
6. **Server verifies token** with Google servers
7. **Google confirms** token is valid
8. **Server creates JWT** and sends to app
9. **User is logged in** to Clara

---

## Part 1: Google Cloud Console Setup

### Step 1: Create or Select a Project

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/

2. **Create a New Project** (or use existing)
   - Click project dropdown at top
   - Click "New Project"
   - **Project Name:** `Clara HVAC` (or your choice)
   - **Organization:** Your organization (or leave blank)
   - Click **"Create"**

3. **Note your Project ID**
   - Example: `clara-hvac-123456`
   - You'll need this later

---

### Step 2: Enable Required APIs

1. **Navigate to APIs & Services**
   - Left menu → "APIs & Services" → "Library"

2. **Enable Google+ API**
   - Search for "Google+ API"
   - Click on it
   - Click **"Enable"**
   - *(This API provides user profile information)*

3. **Enable People API** (Optional but recommended)
   - Search for "People API"
   - Click **"Enable"**
   - *(Provides additional profile data)*

---

### Step 3: Configure OAuth Consent Screen

This is what users see when they authorize Clara.

1. **Go to OAuth Consent Screen**
   - Left menu → "APIs & Services" → "OAuth consent screen"

2. **Choose User Type**
   - Select **"External"** (unless you have a Google Workspace)
   - Click **"Create"**

3. **Fill in App Information**

   **App name:** `Clara - HVAC Assistant`

   **User support email:** `support@clarahvac.com` (your email)

   **App logo:** Upload Clara's logo (120x120 pixels minimum)

   **Application home page:** `https://clarahvac.com`

   **Application privacy policy:** `https://clarahvac.com/privacy`

   **Application terms of service:** `https://clarahvac.com/terms`

   **Authorized domains:**
   - `clarahvac.com`
   - Add any other domains you use

   **Developer contact email:** Your email

4. **Scopes**
   - Click "Add or Remove Scopes"
   - Select these scopes:
     - ✅ `.../auth/userinfo.email` - See your email address
     - ✅ `.../auth/userinfo.profile` - See your personal info
     - ✅ `openid` - Authenticate using OpenID Connect

   - Click **"Update"**

5. **Test Users** (During development)
   - Add email addresses of people who can test
   - Example: `john.tech@gmail.com`, `sarah.supervisor@gmail.com`
   - Click **"Save and Continue"**

6. **Summary**
   - Review everything
   - Click **"Back to Dashboard"**

---

### Step 4: Create OAuth 2.0 Credentials

You need **TWO** sets of credentials:
1. **Web Client** (for clara-server backend)
2. **Android Client** (for clara-react-native mobile app)

#### 4A. Create Web Client (for Backend)

1. **Go to Credentials**
   - Left menu → "APIs & Services" → "Credentials"

2. **Create Credentials**
   - Click **"+ Create Credentials"**
   - Select **"OAuth client ID"**

3. **Configure Web Client**
   - **Application type:** Web application
   - **Name:** `Clara Server (Backend)`

   - **Authorized JavaScript origins:**
     ```
     http://localhost:3000
     https://api.clarahvac.com
     ```

   - **Authorized redirect URIs:**
     ```
     http://localhost:3000/auth/google/callback
     https://api.clarahvac.com/auth/google/callback
     ```

   - Click **"Create"**

4. **Save Your Credentials**

   You'll get:
   - **Client ID:** `123456789-abcdefg.apps.googleusercontent.com`
   - **Client Secret:** `GOCSPX-aBcDeFgHiJkLmNoPqRsTuVwXyZ`

   ⚠️ **IMPORTANT:** Save these securely!

#### 4B. Create Android Client (for Mobile App)

1. **Create Another OAuth Client**
   - Click **"+ Create Credentials"** → **"OAuth client ID"**

2. **Configure Android Client**
   - **Application type:** Android
   - **Name:** `Clara Mobile App (Android)`

   - **Package name:** `com.clarahvac.mobile` (from app.json)

   - **SHA-1 certificate fingerprint:**
     - You need to generate this from your Android signing key
     - See "Getting SHA-1 Fingerprint" section below

3. **Save Android Client ID**
   - **Client ID:** `987654321-xyz.apps.googleusercontent.com`

---

### Step 5: Get SHA-1 Certificate Fingerprint

For Android, Google needs your app's signing certificate fingerprint.

#### For Development (Debug Key)

**On Windows:**
```bash
cd "C:\Users\YourUsername\.android"
keytool -list -v -keystore debug.keystore -alias androiddebugkey -storepass android -keypass android
```

**On Mac/Linux:**
```bash
cd ~/.android
keytool -list -v -keystore debug.keystore -alias androiddebugkey -storepass android -keypass android
```

**Look for:**
```
Certificate fingerprints:
    SHA1: AB:CD:EF:12:34:56:78:90:AB:CD:EF:12:34:56:78:90:AB:CD:EF:12
    SHA256: ...
```

**Copy the SHA1 value** and paste it in Google Console.

#### For Production (Release Key)

You'll need to generate a release keystore:

```bash
keytool -genkeypair -v -storetype PKCS12 -keystore clara-release-key.keystore -alias clara-key -keyalg RSA -keysize 2048 -validity 10000
```

Then get the SHA-1:
```bash
keytool -list -v -keystore clara-release-key.keystore -alias clara-key
```

---

### Step 6: Optional - Create iOS Client

If you plan to support iOS in the future:

1. **Create OAuth Client**
   - Application type: iOS
   - Bundle ID: `com.clarahvac.mobile`

---

## Part 2: Backend Configuration (clara-server)

### Environment Variables

Add to `.env` file:

```bash
# Google OAuth
GOOGLE_CLIENT_ID=123456789-abcdefg.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-aBcDeFgHiJkLmNoPqRsTuVwXyZ
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/google/callback

# JWT Settings
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30
```

### Install Required Packages

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2
pip install python-jose[cryptography]
pip install passlib[bcrypt]
```

Or add to `requirements.txt`:
```
google-auth==2.25.2
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
```

### Code Example: Backend Authentication

**File: `clara-server/auth/google_oauth.py`**

```python
from google.oauth2 import id_token
from google.auth.transport import requests
import os

class GoogleOAuth:
    def __init__(self):
        self.client_id = os.getenv('GOOGLE_CLIENT_ID')

    async def verify_token(self, token: str) -> dict:
        """Verify Google ID token and return user info"""
        try:
            # Verify the token with Google
            idinfo = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                self.client_id
            )

            # Check issuer
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')

            # Token is valid. Get user info
            return {
                'google_id': idinfo['sub'],
                'email': idinfo['email'],
                'email_verified': idinfo.get('email_verified', False),
                'name': idinfo.get('name', ''),
                'picture': idinfo.get('picture', ''),
                'given_name': idinfo.get('given_name', ''),
                'family_name': idinfo.get('family_name', '')
            }

        except ValueError as e:
            # Invalid token
            raise Exception(f"Invalid token: {e}")
```

**File: `clara-server/auth/jwt_handler.py`**

```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
import os

SECRET_KEY = os.getenv('JWT_SECRET_KEY')
ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', 60))

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
```

**File: `clara-server/main.py` (Auth endpoints)**

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from auth.google_oauth import GoogleOAuth
from auth.jwt_handler import create_access_token
from users.service import UserService

router = APIRouter()
google_oauth = GoogleOAuth()
user_service = UserService()

class GoogleLoginRequest(BaseModel):
    id_token: str

@router.post("/auth/google/login")
async def google_login(request: GoogleLoginRequest):
    """Login with Google ID token"""
    try:
        # Verify Google token
        user_info = await google_oauth.verify_token(request.id_token)

        # Check if user exists
        user = await user_service.get_user_by_google_id(user_info['google_id'])

        if not user:
            # Create new user
            user = await user_service.create_user_from_google(user_info)
        else:
            # Update last login
            await user_service.update_last_login(user['user_id'])

        # Create JWT token
        access_token = create_access_token(
            data={
                "user_id": user['user_id'],
                "email": user['email'],
                "role": user['role']
            }
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 3600,
            "user": user
        }

    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
```

---

## Part 3: Frontend Configuration (clara-react-native)

### Install Required Packages

```bash
npx expo install @react-native-google-signin/google-signin
npx expo install @react-native-async-storage/async-storage
npm install jwt-decode
```

### Configure Google Sign-In

**File: `app.json`**

Add to plugins:

```json
{
  "expo": {
    "plugins": [
      "@react-native-google-signin/google-signin"
    ],
    "android": {
      "googleServicesFile": "./google-services.json"
    }
  }
}
```

### Download google-services.json (Android)

1. Go to Firebase Console: https://console.firebase.google.com/
2. Create new project (or use existing)
3. Add Android app
4. Download `google-services.json`
5. Place in root of `clara-react-native/`

### Code Example: React Native Login

**File: `contexts/AuthProvider.tsx`**

```typescript
import React, { createContext, useState, useContext, useEffect } from 'react';
import { GoogleSignin } from '@react-native-google-signin/google-signin';
import AsyncStorage from '@react-native-async-storage/async-storage';
import jwtDecode from 'jwt-decode';

// Configure Google Sign-In
GoogleSignin.configure({
  webClientId: '123456789-abcdefg.apps.googleusercontent.com', // From Google Console
  offlineAccess: true,
});

interface User {
  user_id: string;
  email: string;
  full_name: string;
  role: string;
  profile_picture_url?: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  signInWithGoogle: () => Promise<void>;
  signOut: () => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check for existing token on app start
  useEffect(() => {
    checkExistingAuth();
  }, []);

  const checkExistingAuth = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');

      if (token) {
        const decoded: any = jwtDecode(token);

        // Check if token is expired
        if (decoded.exp * 1000 > Date.now()) {
          // Token valid, fetch user data
          await fetchUserProfile(token);
        } else {
          // Token expired, clear storage
          await AsyncStorage.removeItem('access_token');
        }
      }
    } catch (error) {
      console.error('Error checking auth:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchUserProfile = async (token: string) => {
    try {
      const response = await fetch('http://localhost:3000/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      }
    } catch (error) {
      console.error('Error fetching user:', error);
    }
  };

  const signInWithGoogle = async () => {
    try {
      setIsLoading(true);

      // 1. Sign in with Google
      await GoogleSignin.hasPlayServices();
      const userInfo = await GoogleSignin.signIn();

      // 2. Get ID token
      const tokens = await GoogleSignin.getTokens();

      // 3. Send ID token to backend
      const response = await fetch('http://localhost:3000/auth/google/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          id_token: tokens.idToken
        })
      });

      if (!response.ok) {
        throw new Error('Login failed');
      }

      const data = await response.json();

      // 4. Save access token
      await AsyncStorage.setItem('access_token', data.access_token);

      // 5. Set user in state
      setUser(data.user);

    } catch (error) {
      console.error('Sign in error:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const signOut = async () => {
    try {
      await GoogleSignin.signOut();
      await AsyncStorage.removeItem('access_token');
      setUser(null);
    } catch (error) {
      console.error('Sign out error:', error);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        signInWithGoogle,
        signOut,
        isAuthenticated: !!user
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
```

**File: `app/(auth)/login.tsx`**

```typescript
import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Image } from 'react-native';
import { useAuth } from '@/contexts/AuthProvider';
import { useRouter } from 'expo-router';

export default function LoginScreen() {
  const { signInWithGoogle } = useAuth();
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleGoogleSignIn = async () => {
    try {
      setLoading(true);
      await signInWithGoogle();
      router.replace('/(authenticated)/home');
    } catch (error) {
      console.error('Login failed:', error);
      alert('Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Image
        source={require('@/assets/images/clara-logo.png')}
        style={styles.logo}
      />

      <Text style={styles.title}>Welcome to Clara</Text>
      <Text style={styles.subtitle}>Your AI HVAC Assistant</Text>

      <TouchableOpacity
        style={styles.googleButton}
        onPress={handleGoogleSignIn}
        disabled={loading}
      >
        <Image
          source={require('@/assets/images/google-logo.png')}
          style={styles.googleIcon}
        />
        <Text style={styles.googleButtonText}>
          {loading ? 'Signing in...' : 'Sign in with Google'}
        </Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#1a1a2e',
  },
  logo: {
    width: 120,
    height: 120,
    marginBottom: 30,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 18,
    color: '#a0a0a0',
    marginBottom: 50,
  },
  googleButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 8,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
  },
  googleIcon: {
    width: 24,
    height: 24,
    marginRight: 12,
  },
  googleButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
});
```

---

## Part 4: Testing

### Test on Development

1. **Start Backend:**
   ```bash
   cd clara-server
   uvicorn main:app --reload --port 3000
   ```

2. **Start Mobile App:**
   ```bash
   cd clara-react-native
   npx expo start
   ```

3. **Test Login Flow:**
   - Tap "Sign in with Google"
   - Select your Google account
   - Authorize Clara
   - Should redirect back to app
   - Check console logs for token

### Common Issues & Fixes

**Issue 1: "developer_error" or "invalid_client"**
- **Cause:** Wrong Client ID or SHA-1 fingerprint
- **Fix:** Double-check Client ID in code matches Google Console

**Issue 2: "idpiframe_initialization_failed"**
- **Cause:** Cookies blocked or third-party cookies disabled
- **Fix:** Enable cookies in browser/WebView

**Issue 3: Token verification fails**
- **Cause:** Clock skew or network issues
- **Fix:** Check server time is correct, verify network connectivity

**Issue 4: "Sign in failed"**
- **Cause:** Google Play Services not available (emulator)
- **Fix:** Test on real device or emulator with Google Play

---

## Security Best Practices

### 1. Never Expose Client Secret in Mobile App
❌ **Wrong:**
```typescript
// Don't do this!
const clientSecret = 'GOCSPX-aBcDeFgHiJkLmNoPqRsTuVwXyZ';
```

✅ **Correct:**
- Client secret only in backend `.env` file
- Mobile app only needs Client ID

### 2. Use HTTPS in Production
```python
# .env.production
GOOGLE_REDIRECT_URI=https://api.clarahvac.com/auth/google/callback
```

### 3. Validate Tokens Server-Side
Always verify Google tokens on your backend, never trust the client.

### 4. Set Token Expiration
```python
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60  # 1 hour
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30    # 30 days
```

### 5. Store Tokens Securely
```typescript
// Use AsyncStorage for tokens
await AsyncStorage.setItem('access_token', token);

// Never log tokens
console.log(token); // ❌ Don't do this!
```

---

## Credentials Summary

**You'll need to save these:**

```
PROJECT ID: clara-hvac-123456

WEB CLIENT (Backend):
Client ID: 123456789-abcdefg.apps.googleusercontent.com
Client Secret: GOCSPX-aBcDeFgHiJkLmNoPqRsTuVwXyZ

ANDROID CLIENT (Mobile):
Client ID: 987654321-xyz.apps.googleusercontent.com
Package Name: com.clarahvac.mobile
SHA-1: AB:CD:EF:12:34:56:78:90:...
```

Store these in:
- `.env` file (backend) - **Add to .gitignore!**
- `app.json` or `app.config.js` (mobile)

---

## Next Steps

1. ✅ **Create Google Cloud project**
2. ✅ **Configure OAuth consent screen**
3. ✅ **Create credentials (Web + Android)**
4. ✅ **Add credentials to .env files**
5. ✅ **Install required packages**
6. ✅ **Implement authentication code**
7. ✅ **Test login flow**
8. ✅ **Handle errors gracefully**

---

## Cost

**Google OAuth is FREE** for:
- Unlimited sign-ins
- Standard profile data
- Token verification

You only pay if you use premium Google Workspace APIs.

---

## Questions?

Need help with:
- Setting up Google Cloud project
- Debugging authentication errors
- Understanding the OAuth flow
- Implementing specific features

Just ask! 🚀
