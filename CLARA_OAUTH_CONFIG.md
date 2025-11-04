# Clara OAuth Configuration - Your Setup

## Your Current Domains

✅ **Local Development:** `http://localhost:3000`
✅ **Production/Testing:** `http://deadline.is-very-evil.org:3000`

---

## Google Cloud Console Configuration

### OAuth Consent Screen

**Authorized domains:**
```
deadline.is-very-evil.org
```

*(localhost doesn't need to be added here)*

---

### Web Application Credentials (Backend)

**Name:** `Clara Server (Backend)`

**Authorized JavaScript origins:**
```
http://localhost:3000
http://deadline.is-very-evil.org:3000
```

**Authorized redirect URIs:**
```
http://localhost:3000/auth/google/callback
http://deadline.is-very-evil.org:3000/auth/google/callback
```

---

## Backend Configuration (clara-server)

### File: `.env.local` (for local development)

```bash
# Google OAuth
GOOGLE_CLIENT_ID=YOUR_WEB_CLIENT_ID_HERE
GOOGLE_CLIENT_SECRET=YOUR_CLIENT_SECRET_HERE
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/google/callback

# JWT Settings
JWT_SECRET_KEY=your-super-secret-jwt-key-min-32-characters
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# Database
DATABASE_URL=postgresql://clara:clara_dev_password@localhost:5432/clara

# Backend URL
BACKEND_URL=http://localhost:3000
```

### File: `.env.production` (for deadline.is-very-evil.org)

```bash
# Google OAuth
GOOGLE_CLIENT_ID=YOUR_WEB_CLIENT_ID_HERE
GOOGLE_CLIENT_SECRET=YOUR_CLIENT_SECRET_HERE
GOOGLE_REDIRECT_URI=http://deadline.is-very-evil.org:3000/auth/google/callback

# JWT Settings
JWT_SECRET_KEY=your-super-secret-jwt-key-min-32-characters
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# Database (update with production DB)
DATABASE_URL=postgresql://clara:password@deadline.is-very-evil.org:5432/clara

# Backend URL
BACKEND_URL=http://deadline.is-very-evil.org:3000
```

---

## Frontend Configuration (clara-react-native)

### File: `.env.local` (for local development)

```bash
# Backend API
EXPO_PUBLIC_API_BASE_URL=http://localhost:3000
EXPO_PUBLIC_TOKEN_ENDPOINT=http://localhost:3000/token

# Google OAuth (same Web Client ID)
EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID=YOUR_WEB_CLIENT_ID_HERE
```

### File: `.env.production` (for testing with deadline.is-very-evil.org)

```bash
# Backend API
EXPO_PUBLIC_API_BASE_URL=http://deadline.is-very-evil.org:3000
EXPO_PUBLIC_TOKEN_ENDPOINT=http://deadline.is-very-evil.org:3000/token

# Google OAuth (same Web Client ID)
EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID=YOUR_WEB_CLIENT_ID_HERE
```

### In Code: `contexts/AuthProvider.tsx`

```typescript
import Constants from 'expo-constants';
import { GoogleSignin } from '@react-native-google-signin/google-signin';

// Get from environment
const API_BASE_URL = Constants.expoConfig?.extra?.apiBaseUrl || 'http://localhost:3000';
const WEB_CLIENT_ID = Constants.expoConfig?.extra?.googleWebClientId || 'YOUR_CLIENT_ID';

// Configure Google Sign-In
GoogleSignin.configure({
  webClientId: WEB_CLIENT_ID,
  offlineAccess: true,
});

// API calls
const response = await fetch(`${API_BASE_URL}/auth/google/login`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    id_token: tokens.idToken
  })
});
```

---

## Agent Configuration (clara-agent)

### File: `.env.local`

```bash
# Backend API URL
BACKEND_URL=http://localhost:3000

# LiveKit
LIVEKIT_URL=wss://claranew-00jbylxr.livekit.cloud
LIVEKIT_API_KEY=APIzhuiW5P2MWEb
LIVEKIT_API_SECRET=Yu4nA5ebDfwDoDnFhJL5e7op8fKXAEleq8aquiHFNBRH

# Google AI (Gemini)
GOOGLE_API_KEY=AIzaSyAidzKDrVpP2KI8ffBOY6_VWJc53wSD7AE

# Tavily Search API
TAVILY_API_KEY=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

# Firecrawl API
FIRECRAWL_API_KEY=fc-62f12fd189a9410ead8cb758263ba229
```

---

## Testing URLs

### Local Development

**Backend:** http://localhost:3000
**Health Check:** http://localhost:3000/health
**Login Endpoint:** http://localhost:3000/auth/google/login
**Mobile App:** Points to localhost:3000

### Production/Testing (deadline.is-very-evil.org)

**Backend:** http://deadline.is-very-evil.org:3000
**Health Check:** http://deadline.is-very-evil.org:3000/health
**Login Endpoint:** http://deadline.is-very-evil.org:3000/auth/google/login
**Mobile App:** Points to deadline.is-very-evil.org:3000

---

## Network Configuration for Testing

### Testing Mobile App with Local Backend

If you're testing the mobile app on a physical device with backend on localhost:

**Option 1: Use your computer's local IP**
```bash
# Find your local IP
# Windows: ipconfig
# Mac/Linux: ifconfig

# Use in .env
EXPO_PUBLIC_API_BASE_URL=http://192.168.1.100:3000
```

**Option 2: Use ngrok for tunneling**
```bash
ngrok http 3000
# Use the ngrok URL in mobile app
EXPO_PUBLIC_API_BASE_URL=https://abc123.ngrok.io
```

**Option 3: Use deadline.is-very-evil.org**
```bash
# Deploy backend to deadline.is-very-evil.org
# Use in .env
EXPO_PUBLIC_API_BASE_URL=http://deadline.is-very-evil.org:3000
```

---

## Current Setup (From your .env.local)

Based on your existing configuration:

```bash
# You're currently using:
LIVEKIT_URL=wss://claranew-00jbylxr.livekit.cloud
BACKEND_URL=http://localhost:3000

# Mobile app uses:
TOKEN_ENDPOINT: http://deadline.is-very-evil.org:3000/token
```

**For OAuth, you'll need to add:**

```bash
# In clara-server/.env.local
GOOGLE_CLIENT_ID=<from Google Console>
GOOGLE_CLIENT_SECRET=<from Google Console>
JWT_SECRET_KEY=<generate random string>
```

```bash
# In clara-react-native/.env.local
EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID=<same as backend Client ID>
```

---

## Generate JWT Secret Key

Run this to generate a secure random key:

**Python:**
```python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Or use this:**
```bash
openssl rand -base64 32
```

**Example output:**
```
vK8Zx2Q9mN3pL7jR4fT6yW8eA5hS1dG0cU9bV2nM4xY=
```

Copy this and use as `JWT_SECRET_KEY` in your `.env` file.

---

## Google Console - Exact Configuration

### Step 1: OAuth Consent Screen

```
User Type: External
App name: Clara - HVAC Assistant
User support email: <your-email>

Authorized domains:
  deadline.is-very-evil.org

Developer contact email: <your-email>

Scopes:
  ✓ .../auth/userinfo.email
  ✓ .../auth/userinfo.profile
  ✓ openid
```

### Step 2: Create Web Credentials

```
Application type: Web application
Name: Clara Server

Authorized JavaScript origins:
  http://localhost:3000
  http://deadline.is-very-evil.org:3000

Authorized redirect URIs:
  http://localhost:3000/auth/google/callback
  http://deadline.is-very-evil.org:3000/auth/google/callback
```

Click **CREATE** → Save the Client ID and Client Secret

### Step 3: Create Android Credentials

```
Application type: Android
Name: Clara Mobile App

Package name: com.clarahvac.mobile
SHA-1 certificate fingerprint: <get from keytool>
```

Get SHA-1:
```bash
cd %USERPROFILE%\.android
keytool -list -v -keystore debug.keystore -alias androiddebugkey -storepass android
```

---

## Testing Checklist

### ✅ Backend is Running
```bash
cd clara-server
uvicorn main:app --reload --port 3000

# Test:
curl http://localhost:3000/health
```

### ✅ Environment Variables Set
```bash
# Check .env file has:
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
JWT_SECRET_KEY=...
```

### ✅ Google Console Configured
- OAuth consent screen created
- Web credentials created with correct redirect URIs
- Android credentials created with correct SHA-1

### ✅ Mobile App Configured
```bash
cd clara-react-native
# Check .env has:
EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID=...
EXPO_PUBLIC_API_BASE_URL=http://deadline.is-very-evil.org:3000
```

### ✅ Test Login Flow
1. Start backend: `uvicorn main:app --reload`
2. Start mobile: `npx expo start`
3. Tap "Sign in with Google"
4. Should see Google authorization screen
5. After approval, should log in successfully

---

## Quick Commands

### Start Everything

**Terminal 1 - Backend:**
```bash
cd D:\lean\clara-server
uvicorn main:app --reload --host 0.0.0.0 --port 3000
```

**Terminal 2 - Agent:**
```bash
cd D:\lean\clara-agent
uv run python src/agent.py dev
```

**Terminal 3 - Mobile:**
```bash
cd D:\lean\clara-react-native
npx expo start
```

---

## Important Notes

### About deadline.is-very-evil.org

✅ **Pros:**
- Already set up
- Accessible from anywhere
- Works for testing on real devices

⚠️ **Cons:**
- HTTP (not HTTPS) - Google allows this for testing
- For production, you'll want HTTPS

### When You Get a Real Domain

When you get `clarahvac.com` (or similar):

1. **Update Google Console:**
   - Add new domain to authorized domains
   - Add new redirect URIs with new domain
   - Keep old ones for backward compatibility

2. **Update .env files:**
   - Change `deadline.is-very-evil.org` to `clarahvac.com`
   - Use HTTPS: `https://clarahvac.com`

3. **Zero code changes needed!**
   - Everything reads from environment variables
   - Just update .env and restart

---

## Next Steps

1. **Go to Google Cloud Console**
   - https://console.cloud.google.com/

2. **Create Project**
   - Name: "Clara HVAC"

3. **Configure OAuth**
   - Use the exact settings above
   - Copy your domain: `deadline.is-very-evil.org`

4. **Get Credentials**
   - Web Client ID + Secret
   - Android Client ID

5. **Add to .env files**
   - clara-server/.env.local
   - clara-react-native/.env.local

6. **Test!**
   - Start backend + mobile
   - Try logging in

Ready to set it up? Let me know if you need help with any step!
