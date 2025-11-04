# Google OAuth - Quick Reference Card

## 🎯 Essential Steps (15 minutes)

### 1️⃣ Google Cloud Console (5 min)

**Create Project:**
- Go to: https://console.cloud.google.com/
- New Project → Name: `Clara HVAC`
- Note Project ID

**Enable APIs:**
- APIs & Services → Library
- Enable: `Google+ API`

**OAuth Consent Screen:**
- External user type
- App name: `Clara - HVAC Assistant`
- Scopes: `email`, `profile`, `openid`

### 2️⃣ Create Credentials (5 min)

**Web Application (Backend):**
```
Type: Web application
Name: Clara Server
Redirect URI: http://localhost:3000/auth/google/callback
```
**Save:** Client ID + Client Secret

**Android (Mobile App):**
```
Type: Android
Package: com.clarahvac.mobile
SHA-1: [Get from keytool - see below]
```
**Save:** Client ID

### 3️⃣ Get Android SHA-1 (2 min)

**Windows:**
```bash
cd %USERPROFILE%\.android
keytool -list -v -keystore debug.keystore -alias androiddebugkey -storepass android
```

**Mac/Linux:**
```bash
cd ~/.android
keytool -list -v -keystore debug.keystore -alias androiddebugkey -storepass android
```

**Copy the SHA1 line** and paste in Google Console Android credentials.

### 4️⃣ Backend Setup (2 min)

**File: `clara-server/.env`**
```bash
GOOGLE_CLIENT_ID=YOUR_WEB_CLIENT_ID_HERE
GOOGLE_CLIENT_SECRET=YOUR_CLIENT_SECRET_HERE
JWT_SECRET_KEY=generate-random-secret-key-here
```

**Install packages:**
```bash
pip install google-auth python-jose[cryptography]
```

### 5️⃣ Mobile Setup (1 min)

**File: `clara-react-native/app.json`**
```json
{
  "expo": {
    "plugins": ["@react-native-google-signin/google-signin"]
  }
}
```

**Install packages:**
```bash
npx expo install @react-native-google-signin/google-signin
npx expo install @react-native-async-storage/async-storage
```

**Configure in code:**
```typescript
GoogleSignin.configure({
  webClientId: 'YOUR_WEB_CLIENT_ID_HERE',
});
```

---

## 📋 Credentials Checklist

Copy this template and fill in your values:

```
✅ Google Cloud Project ID: _______________________

✅ Web Client ID: _______________________
✅ Web Client Secret: _______________________

✅ Android Client ID: _______________________
✅ Android Package Name: com.clarahvac.mobile
✅ Android SHA-1: _______________________

✅ JWT Secret Key: _______________________
```

---

## 🚀 Test the Flow

1. Start backend: `uvicorn main:app --reload`
2. Start mobile: `npx expo start`
3. Tap "Sign in with Google"
4. Select account → Authorize
5. Check console for success!

---

## ⚠️ Common Errors

| Error | Solution |
|-------|----------|
| `developer_error` | Wrong Client ID - check it matches |
| `invalid_client` | Wrong SHA-1 fingerprint - regenerate |
| `401 Unauthorized` | Token expired - implement refresh |
| Sign in failed | Google Play Services missing - use real device |

---

## 🔐 Security Reminders

- ✅ Client Secret **ONLY** in backend `.env`
- ✅ Add `.env` to `.gitignore`
- ✅ Use HTTPS in production
- ✅ Never log tokens
- ✅ Set token expiration (1 hour)

---

## 📚 Full Documentation

See `GOOGLE_OAUTH_SETUP_GUIDE.md` for:
- Detailed explanations
- Code examples
- Troubleshooting
- Security best practices
- Testing strategies

---

## 🆘 Need Help?

**Common Questions:**

**Q: Where do I find my SHA-1?**
A: Run `keytool -list -v -keystore ~/.android/debug.keystore`

**Q: Which Client ID goes where?**
A: Web Client ID → Both backend AND mobile app
   Android Client ID → Just for Google to recognize your app

**Q: Do I need Firebase?**
A: Not required, but recommended for easier setup

**Q: What about iOS?**
A: Create iOS OAuth client later when needed

---

## ⏱️ Time Investment

- **First time:** ~15 minutes
- **Subsequent projects:** ~5 minutes
- **ROI:** Infinite - never build your own auth again!

---

## 🎁 Benefits

✅ No password management
✅ Users already trust Google
✅ Auto-filled profile data
✅ One-tap sign in
✅ Free forever
✅ Industry standard

---

Ready to implement? Start with Step 1! 🚀
