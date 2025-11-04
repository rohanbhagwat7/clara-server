# Google OAuth Setup - Automated with gcloud CLI

This guide automates the entire Google OAuth setup using the gcloud CLI, perfect for quickly setting up test users without manual Google Console work.

---

## Prerequisites

### 1. Install Google Cloud SDK

**Windows:**
```bash
# Download and run installer
https://cloud.google.com/sdk/docs/install#windows

# Or use PowerShell
(New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:Temp\GoogleCloudSDKInstaller.exe")
& $env:Temp\GoogleCloudSDKInstaller.exe
```

**Verify installation:**
```bash
gcloud --version
```

### 2. Authenticate with Google Cloud

```bash
gcloud auth login
```

This opens a browser for you to sign in with your Google account.

---

## Automated Setup Script

### Step 1: Set Variables

```bash
# Project Configuration
export PROJECT_ID="clara-hvac-$(date +%s)"  # Unique project ID
export PROJECT_NAME="Clara HVAC"
export REGION="us-central1"

# OAuth Configuration
export APP_NAME="Clara - HVAC Assistant"
export SUPPORT_EMAIL="your-email@gmail.com"  # CHANGE THIS

# Your Domains
export LOCAL_DOMAIN="http://localhost:3000"
export PROD_DOMAIN="http://deadline.is-very-evil.org:3000"

# Test Users (CHANGE THESE)
export TEST_USER_1="john.tech@gmail.com"
export TEST_USER_2="sarah.supervisor@gmail.com"
export TEST_USER_3="admin@gmail.com"
```

**For Windows PowerShell:**
```powershell
# Project Configuration
$PROJECT_ID = "clara-hvac-$(Get-Date -UFormat %s)"
$PROJECT_NAME = "Clara HVAC"
$REGION = "us-central1"

# OAuth Configuration
$APP_NAME = "Clara - HVAC Assistant"
$SUPPORT_EMAIL = "your-email@gmail.com"  # CHANGE THIS

# Your Domains
$LOCAL_DOMAIN = "http://localhost:3000"
$PROD_DOMAIN = "http://deadline.is-very-evil.org:3000"

# Test Users (CHANGE THESE)
$TEST_USER_1 = "john.tech@gmail.com"
$TEST_USER_2 = "sarah.supervisor@gmail.com"
$TEST_USER_3 = "admin@gmail.com"
```

---

### Step 2: Create Project

```bash
# Create new project
gcloud projects create $PROJECT_ID --name="$PROJECT_NAME"

# Set as active project
gcloud config set project $PROJECT_ID

# Link billing account (required for APIs)
# List billing accounts first
gcloud billing accounts list

# Link billing (replace BILLING_ACCOUNT_ID with actual ID from above)
gcloud billing projects link $PROJECT_ID --billing-account=BILLING_ACCOUNT_ID
```

**Windows PowerShell:**
```powershell
gcloud projects create $PROJECT_ID --name=$PROJECT_NAME
gcloud config set project $PROJECT_ID
gcloud billing accounts list
# Note the billing account ID, then run:
# gcloud billing projects link $PROJECT_ID --billing-account=YOUR_BILLING_ACCOUNT_ID
```

---

### Step 3: Enable Required APIs

```bash
# Enable Google+ API (for OAuth)
gcloud services enable plus.googleapis.com

# Enable other useful APIs
gcloud services enable iamcredentials.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com
```

---

### Step 4: Configure OAuth Consent Screen

**Unfortunately, OAuth consent screen configuration is not fully supported via gcloud CLI.**

You'll need to configure this manually **once**, but it's very quick:

1. Go to: https://console.cloud.google.com/apis/credentials/consent
2. Select project: **$PROJECT_ID** (displayed in your terminal)
3. Choose **External** user type → Click **Create**
4. Fill in:
   - App name: **Clara - HVAC Assistant**
   - User support email: Your email
   - Authorized domains: **deadline.is-very-evil.org**
   - Developer contact: Your email
5. Click **Save and Continue**
6. Scopes page → Click **Add or Remove Scopes**
   - Select: `userinfo.email`, `userinfo.profile`, `openid`
   - Click **Update** → **Save and Continue**
7. **Test users page** → Click **Add Users**
   - Add your test user emails:
     - john.tech@gmail.com
     - sarah.supervisor@gmail.com
     - admin@gmail.com
   - Click **Add** → **Save and Continue**
8. Summary page → Click **Back to Dashboard**

**This is the only manual step**, but takes ~2 minutes.

---

### Step 5: Create OAuth Credentials (CLI)

#### Create Web Application Credentials

```bash
# Create OAuth client
gcloud alpha iap oauth-clients create \
  --project=$PROJECT_ID \
  --brand=$PROJECT_ID \
  projects/$PROJECT_ID/brands/default

# Note: This creates the brand. Now we need to create the actual OAuth client.
# Unfortunately, we need to use gcloud auth application-default or manual creation

# The easiest way is to use a script with gcloud
```

**Actually, let's use the REST API via curl:**

```bash
# Get access token
ACCESS_TOKEN=$(gcloud auth print-access-token)

# Create Web OAuth Client
curl -X POST \
  "https://oauth2.googleapis.com/v2/oauth/clients" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"client_id\": \"$PROJECT_ID.apps.googleusercontent.com\",
    \"client_secret\": \"$(openssl rand -base64 32)\",
    \"redirect_uris\": [
      \"$LOCAL_DOMAIN/auth/google/callback\",
      \"$PROD_DOMAIN/auth/google/callback\"
    ],
    \"auth_uri\": \"https://accounts.google.com/o/oauth2/auth\",
    \"token_uri\": \"https://oauth2.googleapis.com/token\",
    \"javascript_origins\": [
      \"$LOCAL_DOMAIN\",
      \"$PROD_DOMAIN\"
    ]
  }"
```

---

## Simplified Approach: Semi-Automated Setup

Since gcloud CLI doesn't fully support OAuth client creation, here's a **hybrid approach** that's fastest:

### 1. Create Project via CLI (30 seconds)

```bash
# Set variables
PROJECT_ID="clara-hvac-$(date +%s)"
PROJECT_NAME="Clara HVAC"

# Create project
gcloud projects create $PROJECT_ID --name="$PROJECT_NAME"
gcloud config set project $PROJECT_ID

# Enable APIs
gcloud services enable plus.googleapis.com

echo "✅ Project created: $PROJECT_ID"
echo "🔗 Open Google Console: https://console.cloud.google.com/apis/credentials?project=$PROJECT_ID"
```

**Windows PowerShell:**
```powershell
$PROJECT_ID = "clara-hvac-$((Get-Date).ToFileTime())"
gcloud projects create $PROJECT_ID --name="Clara HVAC"
gcloud config set project $PROJECT_ID
gcloud services enable plus.googleapis.com
Write-Host "✅ Project created: $PROJECT_ID"
Write-Host "🔗 Open: https://console.cloud.google.com/apis/credentials?project=$PROJECT_ID"
```

---

### 2. Quick Manual Setup in Google Console (3 minutes)

Open the URL printed above, then:

#### A. Configure OAuth Consent Screen

1. Click **Configure Consent Screen**
2. **External** → **Create**
3. Fill in:
   ```
   App name: Clara - HVAC Assistant
   User support email: <your-email>
   Authorized domains: deadline.is-very-evil.org
   Developer contact: <your-email>
   ```
4. **Save and Continue**
5. Scopes → **Add or Remove Scopes**
   - Select: ✓ `email`, ✓ `profile`, ✓ `openid`
   - **Update** → **Save and Continue**
6. **Test users** → **Add Users**
   - Add test emails (e.g., john.tech@gmail.com)
   - **Add** → **Save and Continue**
7. **Back to Dashboard**

#### B. Create Web Credentials

1. Click **Create Credentials** → **OAuth client ID**
2. Application type: **Web application**
3. Name: `Clara Server`
4. **Authorized JavaScript origins:**
   ```
   http://localhost:3000
   http://deadline.is-very-evil.org:3000
   ```
5. **Authorized redirect URIs:**
   ```
   http://localhost:3000/auth/google/callback
   http://deadline.is-very-evil.org:3000/auth/google/callback
   ```
6. **Create**
7. **Copy Client ID and Client Secret** (save them!)

#### C. Create Android Credentials (Optional for now)

Skip this until you need to test on real Android device.

---

### 3. Extract Credentials via CLI

```bash
# List OAuth clients (after creation)
gcloud alpha iap oauth-clients list --project=$PROJECT_ID

# Describe specific client (replace CLIENT_ID)
gcloud alpha iap oauth-clients describe CLIENT_ID --project=$PROJECT_ID
```

---

## Complete Setup Script (Windows PowerShell)

Save this as `setup-oauth.ps1`:

```powershell
# Clara OAuth Setup Script
# Run this in PowerShell

Write-Host "🚀 Clara HVAC - Google OAuth Setup" -ForegroundColor Cyan
Write-Host ""

# Check if gcloud is installed
if (!(Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "❌ gcloud CLI not found!" -ForegroundColor Red
    Write-Host "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
}

# Configuration
$PROJECT_ID = "clara-hvac-$((Get-Date).ToFileTime())"
$PROJECT_NAME = "Clara HVAC"

Write-Host "📋 Configuration:" -ForegroundColor Yellow
Write-Host "   Project ID: $PROJECT_ID"
Write-Host "   Project Name: $PROJECT_NAME"
Write-Host ""

# Authenticate
Write-Host "🔐 Authenticating with Google Cloud..." -ForegroundColor Cyan
gcloud auth login

# Create project
Write-Host "📦 Creating Google Cloud project..." -ForegroundColor Cyan
gcloud projects create $PROJECT_ID --name=$PROJECT_NAME

# Set active project
gcloud config set project $PROJECT_ID

# Enable APIs
Write-Host "⚙️  Enabling required APIs..." -ForegroundColor Cyan
gcloud services enable plus.googleapis.com
gcloud services enable iamcredentials.googleapis.com

Write-Host ""
Write-Host "✅ Project setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Configure OAuth Consent Screen (2 min):"
Write-Host "   https://console.cloud.google.com/apis/credentials/consent?project=$PROJECT_ID" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Create OAuth Credentials (1 min):"
Write-Host "   https://console.cloud.google.com/apis/credentials?project=$PROJECT_ID" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Add test users:" -ForegroundColor White
Write-Host "   - john.tech@gmail.com (technician)"
Write-Host "   - sarah.supervisor@gmail.com (supervisor)"
Write-Host "   - admin@gmail.com (admin)"
Write-Host ""
Write-Host "4. Copy Client ID and Secret to .env files"
Write-Host ""

# Save project ID to file
$PROJECT_ID | Out-File -FilePath "google-project-id.txt"
Write-Host "💾 Project ID saved to: google-project-id.txt" -ForegroundColor Green
```

**Run it:**
```powershell
powershell -ExecutionPolicy Bypass -File setup-oauth.ps1
```

---

## Complete Setup Script (Bash/Linux/Mac)

Save this as `setup-oauth.sh`:

```bash
#!/bin/bash

# Clara OAuth Setup Script
# Run this in Terminal

echo "🚀 Clara HVAC - Google OAuth Setup"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found!"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Configuration
PROJECT_ID="clara-hvac-$(date +%s)"
PROJECT_NAME="Clara HVAC"

echo "📋 Configuration:"
echo "   Project ID: $PROJECT_ID"
echo "   Project Name: $PROJECT_NAME"
echo ""

# Authenticate
echo "🔐 Authenticating with Google Cloud..."
gcloud auth login

# Create project
echo "📦 Creating Google Cloud project..."
gcloud projects create $PROJECT_ID --name="$PROJECT_NAME"

# Set active project
gcloud config set project $PROJECT_ID

# Enable APIs
echo "⚙️  Enabling required APIs..."
gcloud services enable plus.googleapis.com
gcloud services enable iamcredentials.googleapis.com

echo ""
echo "✅ Project setup complete!"
echo ""
echo "📝 Next Steps:"
echo "1. Configure OAuth Consent Screen (2 min):"
echo "   https://console.cloud.google.com/apis/credentials/consent?project=$PROJECT_ID"
echo ""
echo "2. Create OAuth Credentials (1 min):"
echo "   https://console.cloud.google.com/apis/credentials?project=$PROJECT_ID"
echo ""
echo "3. Add test users:"
echo "   - john.tech@gmail.com (technician)"
echo "   - sarah.supervisor@gmail.com (supervisor)"
echo "   - admin@gmail.com (admin)"
echo ""
echo "4. Copy Client ID and Secret to .env files"
echo ""

# Save project ID to file
echo $PROJECT_ID > google-project-id.txt
echo "💾 Project ID saved to: google-project-id.txt"
```

**Run it:**
```bash
chmod +x setup-oauth.sh
./setup-oauth.sh
```

---

## After Credentials are Created

### 1. Update Backend Environment Variables

**File: `clara-server/.env.local`**

```bash
# Google OAuth
GOOGLE_CLIENT_ID=123456789-abcdefg.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-secret-here
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/google/callback

# JWT Settings
JWT_SECRET_KEY=$(openssl rand -base64 32)
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# Database
DATABASE_URL=postgresql://clara:clara_dev_password@localhost:5432/clara

# Backend URL
BACKEND_URL=http://localhost:3000
```

**Generate JWT Secret:**
```bash
# Linux/Mac
openssl rand -base64 32

# Windows PowerShell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

### 2. Update Frontend Environment Variables

**File: `clara-react-native/.env.local`**

```bash
# Backend API
EXPO_PUBLIC_API_BASE_URL=http://deadline.is-very-evil.org:3000
EXPO_PUBLIC_TOKEN_ENDPOINT=http://deadline.is-very-evil.org:3000/token

# Google OAuth (same Web Client ID as backend)
EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID=123456789-abcdefg.apps.googleusercontent.com
```

---

### 3. Install Required Packages

**Backend:**
```bash
cd clara-server
pip install google-auth google-auth-oauthlib python-jose[cryptography] passlib[bcrypt]
```

**Frontend:**
```bash
cd clara-react-native
npx expo install @react-native-google-signin/google-signin
npx expo install @react-native-async-storage/async-storage
```

---

## Test the OAuth Flow

### 1. Start Backend

```bash
cd clara-server
uvicorn main:app --reload --host 0.0.0.0 --port 3000
```

### 2. Start Mobile App

```bash
cd clara-react-native
npx expo start
```

### 3. Test Login

1. Open mobile app
2. Tap "Sign in with Google"
3. Select one of your test users
4. Approve permissions
5. Should redirect back to app logged in

---

## Managing Test Users

### Add Test User via Console

1. Go to: https://console.cloud.google.com/apis/credentials/consent
2. Select your project
3. Scroll to **Test users** section
4. Click **Add Users**
5. Enter email address
6. Click **Add**

### Remove Test User

1. Same page as above
2. Click the ❌ next to the user email
3. Confirm removal

---

## Common Issues

### "Access Blocked: This app's request is invalid"

**Cause:** Redirect URI mismatch

**Solution:**
1. Check authorized redirect URIs match exactly
2. No trailing slashes
3. Use correct port number (3000)

### "developer_error"

**Cause:** Wrong Client ID in mobile app

**Solution:**
Ensure `EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID` matches the **Web Client ID** (not Android Client ID)

### "Sign-in failed"

**Cause:** User not in test users list

**Solution:**
Add the user email to test users in OAuth consent screen

---

## Production Checklist

When moving to production:

1. **Publish OAuth Consent Screen**
   - Console → OAuth consent screen
   - Click **Publish App**
   - Submit for verification (if needed)

2. **Add HTTPS**
   - Get SSL certificate
   - Update all URLs to https://
   - Update Google Console redirect URIs

3. **Update Domains**
   - Add production domain to authorized domains
   - Add production redirect URIs
   - Update all .env files

4. **Remove Test Users**
   - Once published, all Google users can sign in
   - Remove test user restrictions

---

## Quick Reference

### Useful gcloud Commands

```bash
# List all projects
gcloud projects list

# Switch project
gcloud config set project PROJECT_ID

# List enabled APIs
gcloud services list --enabled

# View current configuration
gcloud config list

# List OAuth clients
gcloud alpha iap oauth-clients list

# Get project number
gcloud projects describe PROJECT_ID --format="value(projectNumber)"
```

---

## Estimated Time

- **Automated script**: 30 seconds
- **Manual OAuth setup**: 3 minutes
- **Update .env files**: 1 minute
- **Test login**: 1 minute

**Total: ~5 minutes** from start to working OAuth! 🎉

---

## Need Help?

If you encounter issues:

1. Check that test user emails are added in OAuth consent screen
2. Verify Client ID matches in both backend and frontend
3. Ensure redirect URIs match exactly (no trailing slashes)
4. Check that Google+ API is enabled
5. Try with different test user email

---

## Next Steps After OAuth Works

1. Implement Phase 1 of conversation intelligence (see IMPLEMENTATION_PLAN_CONVO_INT.md)
2. Create user roles and permissions
3. Build supervisor-technician assignments
4. Start Phase 2: Conversation recording

Ready to build! 🚀
