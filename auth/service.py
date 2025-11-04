"""Authentication service - Google OAuth and JWT"""
import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict
import psycopg
from jose import jwt, JWTError
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from dotenv import load_dotenv

load_dotenv()
load_dotenv('.env.local')

# Configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', '60'))
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRE_DAYS', '30'))
DATABASE_URL = os.getenv('DATABASE_URL')


class AuthService:
    """Authentication service for Google OAuth and JWT"""

    def __init__(self):
        self.google_client_id = GOOGLE_CLIENT_ID
        self.jwt_secret = JWT_SECRET_KEY
        self.jwt_algorithm = JWT_ALGORITHM
        self.access_token_expire_minutes = JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = JWT_REFRESH_TOKEN_EXPIRE_DAYS

    def verify_google_token(self, id_token_str: str) -> Dict:
        """
        Verify Google ID token and return user info

        Returns:
            dict with keys: google_id, email, name, picture
        """
        try:
            # Verify the token with clock skew tolerance
            idinfo = id_token.verify_oauth2_token(
                id_token_str,
                google_requests.Request(),
                self.google_client_id,
                clock_skew_in_seconds=10  # Allow 10 seconds clock skew tolerance
            )

            # Extract user info
            return {
                'google_id': idinfo['sub'],
                'email': idinfo['email'],
                'name': idinfo.get('name', ''),
                'picture': idinfo.get('picture', '')
            }
        except ValueError as e:
            # Invalid token
            raise ValueError(f"Invalid Google ID token: {e}")

    def get_or_create_user(self, google_info: Dict) -> Dict:
        """
        Get existing user or create new one from Google info

        Returns:
            dict with user data
        """
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # Check if user exists by google_id
                cur.execute("""
                    SELECT user_id, email, full_name, role, google_id,
                           profile_picture_url, phone, created_at, last_login
                    FROM users
                    WHERE google_id = %s
                """, (google_info['google_id'],))

                user = cur.execute("""
                    SELECT user_id, email, full_name, role, google_id,
                           profile_picture_url, phone, created_at, last_login
                    FROM users
                    WHERE google_id = %s
                """, (google_info['google_id'],)).fetchone()

                if user:
                    # Update last login
                    cur.execute("""
                        UPDATE users
                        SET last_login = NOW()
                        WHERE google_id = %s
                    """, (google_info['google_id'],))
                    conn.commit()

                    return {
                        'user_id': user[0],
                        'email': user[1],
                        'full_name': user[2],
                        'role': user[3],
                        'google_id': user[4],
                        'profile_picture_url': user[5],
                        'phone': user[6],
                        'created_at': user[7],
                        'last_login': user[8]
                    }
                else:
                    # Create new user
                    user_id = f"USER-{secrets.token_hex(6).upper()}"

                    cur.execute("""
                        INSERT INTO users (
                            user_id, email, full_name, google_id,
                            profile_picture_url, role, created_at, last_login
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                        RETURNING user_id, email, full_name, role, google_id,
                                  profile_picture_url, phone, created_at, last_login
                    """, (
                        user_id,
                        google_info['email'],
                        google_info['name'],
                        google_info['google_id'],
                        google_info['picture'],
                        'technician'  # Default role
                    ))

                    new_user = cur.fetchone()
                    conn.commit()

                    return {
                        'user_id': new_user[0],
                        'email': new_user[1],
                        'full_name': new_user[2],
                        'role': new_user[3],
                        'google_id': new_user[4],
                        'profile_picture_url': new_user[5],
                        'phone': new_user[6],
                        'created_at': new_user[7],
                        'last_login': new_user[8]
                    }

    def create_access_token(self, user_id: str, email: str, role: str) -> str:
        """Create JWT access token"""
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode = {
            'sub': user_id,
            'email': email,
            'role': role,
            'exp': expire,
            'type': 'access'
        }
        encoded_jwt = jwt.encode(to_encode, self.jwt_secret, algorithm=self.jwt_algorithm)
        return encoded_jwt

    def create_refresh_token(self, user_id: str) -> str:
        """Create JWT refresh token"""
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode = {
            'sub': user_id,
            'exp': expire,
            'type': 'refresh'
        }
        encoded_jwt = jwt.encode(to_encode, self.jwt_secret, algorithm=self.jwt_algorithm)
        return encoded_jwt

    def store_refresh_token(self, user_id: str, refresh_token: str):
        """Store refresh token in database"""
        # Use SHA256 for token hashing (JWT tokens are too long for bcrypt's 72 byte limit)
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        token_id = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)

        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO auth_tokens (token_id, user_id, token_hash, expires_at)
                    VALUES (%s, %s, %s, %s)
                """, (token_id, user_id, token_hash, expires_at))
                conn.commit()

    def verify_access_token(self, token: str) -> Optional[Dict]:
        """Verify JWT access token and return payload"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            if payload.get('type') != 'access':
                return None
            return payload
        except JWTError:
            return None

    def verify_refresh_token(self, token: str) -> Optional[str]:
        """Verify refresh token and return user_id"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            if payload.get('type') != 'refresh':
                return None

            user_id = payload.get('sub')

            # Check if token exists in database and is not expired
            with psycopg.connect(DATABASE_URL) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT token_hash, expires_at
                        FROM auth_tokens
                        WHERE user_id = %s AND expires_at > NOW()
                    """, (user_id,))

                    tokens = cur.fetchall()

                    # Verify token hash matches (using SHA256)
                    token_hash = hashlib.sha256(token.encode()).hexdigest()
                    for stored_hash, expires_at in tokens:
                        if token_hash == stored_hash:
                            return user_id

                    return None
        except JWTError:
            return None

    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT user_id, email, full_name, role, google_id,
                           profile_picture_url, phone, created_at, last_login
                    FROM users
                    WHERE user_id = %s
                """, (user_id,))

                user = cur.fetchone()

                if user:
                    return {
                        'user_id': user[0],
                        'email': user[1],
                        'full_name': user[2],
                        'role': user[3],
                        'google_id': user[4],
                        'profile_picture_url': user[5],
                        'phone': user[6],
                        'created_at': user[7],
                        'last_login': user[8]
                    }
                return None

    def logout(self, user_id: str, refresh_token: str):
        """Invalidate refresh token"""
        # Hash the refresh token to find it in the database
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()

        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # Delete the specific token
                cur.execute("""
                    DELETE FROM auth_tokens
                    WHERE user_id = %s AND token_hash = %s
                """, (user_id, token_hash))
                conn.commit()


# Global instance
_auth_service = None


def get_auth_service() -> AuthService:
    """Get or create auth service instance"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
