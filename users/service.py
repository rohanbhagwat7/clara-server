"""User and team management service"""
import psycopg
from typing import List, Dict, Optional
from dotenv import load_dotenv
import os

load_dotenv()
load_dotenv('.env.local')

DATABASE_URL = os.getenv('DATABASE_URL')


class UserService:
    """Service for user and team management"""

    def __init__(self):
        self.database_url = DATABASE_URL

    async def get_all_users(self) -> List[Dict]:
        """Get all users"""
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT user_id, email, full_name, role, google_id,
                           profile_picture_url, phone, created_at, last_login, is_active
                    FROM users
                    ORDER BY created_at DESC
                """)
                users = cur.fetchall()

                return [
                    {
                        'user_id': user[0],
                        'email': user[1],
                        'full_name': user[2],
                        'role': user[3],
                        'google_id': user[4],
                        'profile_picture_url': user[5],
                        'phone': user[6],
                        'created_at': user[7].isoformat() if user[7] else None,
                        'last_login': user[8].isoformat() if user[8] else None,
                        'is_active': user[9]
                    }
                    for user in users
                ]

    async def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT user_id, email, full_name, role, google_id,
                           profile_picture_url, phone, created_at, last_login, is_active
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
                        'created_at': user[7].isoformat() if user[7] else None,
                        'last_login': user[8].isoformat() if user[8] else None,
                        'is_active': user[9]
                    }
                return None

    async def update_user_role(self, user_id: str, role: str) -> bool:
        """Update user role"""
        valid_roles = ['technician', 'supervisor', 'admin']
        if role not in valid_roles:
            raise ValueError(f"Invalid role. Must be one of: {', '.join(valid_roles)}")

        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE users
                    SET role = %s
                    WHERE user_id = %s
                """, (role, user_id))
                conn.commit()
                return cur.rowcount > 0

    async def get_technicians(self) -> List[Dict]:
        """Get all technicians"""
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT user_id, email, full_name, profile_picture_url,
                           phone, created_at, last_login, is_active
                    FROM users
                    WHERE role = 'technician' AND is_active = true
                    ORDER BY full_name
                """)
                users = cur.fetchall()

                return [
                    {
                        'user_id': user[0],
                        'email': user[1],
                        'full_name': user[2],
                        'profile_picture_url': user[3],
                        'phone': user[4],
                        'created_at': user[5].isoformat() if user[5] else None,
                        'last_login': user[6].isoformat() if user[6] else None,
                        'is_active': user[7]
                    }
                    for user in users
                ]

    async def get_supervisors(self) -> List[Dict]:
        """Get all supervisors"""
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT user_id, email, full_name, profile_picture_url,
                           phone, created_at, last_login, is_active
                    FROM users
                    WHERE role = 'supervisor' AND is_active = true
                    ORDER BY full_name
                """)
                users = cur.fetchall()

                return [
                    {
                        'user_id': user[0],
                        'email': user[1],
                        'full_name': user[2],
                        'profile_picture_url': user[3],
                        'phone': user[4],
                        'created_at': user[5].isoformat() if user[5] else None,
                        'last_login': user[6].isoformat() if user[6] else None,
                        'is_active': user[7]
                    }
                    for user in users
                ]

    async def get_all_teams(self) -> List[Dict]:
        """Get all teams"""
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT team_id, name, created_at, settings
                    FROM teams
                    ORDER BY name
                """)
                teams = cur.fetchall()

                return [
                    {
                        'team_id': team[0],
                        'name': team[1],
                        'created_at': team[2].isoformat() if team[2] else None,
                        'settings': team[3]
                    }
                    for team in teams
                ]

    async def create_team(self, name: str, settings: Optional[Dict] = None) -> Dict:
        """Create a new team"""
        import secrets
        team_id = f"TEAM-{secrets.token_hex(6).upper()}"

        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO teams (team_id, name, settings)
                    VALUES (%s, %s, %s)
                    RETURNING team_id, name, created_at, settings
                """, (team_id, name, psycopg.types.json.Jsonb(settings or {})))

                team = cur.fetchone()
                conn.commit()

                return {
                    'team_id': team[0],
                    'name': team[1],
                    'created_at': team[2].isoformat() if team[2] else None,
                    'settings': team[3]
                }

    async def get_team_members(self, team_id: str) -> List[Dict]:
        """Get all members of a team"""
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT u.user_id, u.email, u.full_name, u.role,
                           u.profile_picture_url, u.phone,
                           tm.role as team_role, tm.joined_at
                    FROM team_members tm
                    JOIN users u ON tm.user_id = u.user_id
                    WHERE tm.team_id = %s AND u.is_active = true
                    ORDER BY u.full_name
                """, (team_id,))

                members = cur.fetchall()

                return [
                    {
                        'user_id': member[0],
                        'email': member[1],
                        'full_name': member[2],
                        'role': member[3],
                        'profile_picture_url': member[4],
                        'phone': member[5],
                        'team_role': member[6],
                        'joined_at': member[7].isoformat() if member[7] else None
                    }
                    for member in members
                ]

    async def add_team_member(self, team_id: str, user_id: str, role: str = 'member') -> bool:
        """Add a user to a team"""
        valid_roles = ['member', 'supervisor', 'admin']
        if role not in valid_roles:
            raise ValueError(f"Invalid team role. Must be one of: {', '.join(valid_roles)}")

        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute("""
                        INSERT INTO team_members (team_id, user_id, role)
                        VALUES (%s, %s, %s)
                    """, (team_id, user_id, role))
                    conn.commit()
                    return True
                except psycopg.errors.UniqueViolation:
                    return False

    async def remove_team_member(self, team_id: str, user_id: str) -> bool:
        """Remove a user from a team"""
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM team_members
                    WHERE team_id = %s AND user_id = %s
                """, (team_id, user_id))
                conn.commit()
                return cur.rowcount > 0

    async def assign_supervisor(self, supervisor_id: str, technician_id: str) -> bool:
        """Assign a supervisor to a technician"""
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute("""
                        INSERT INTO supervisor_assignments (supervisor_id, technician_id)
                        VALUES (%s, %s)
                    """, (supervisor_id, technician_id))
                    conn.commit()
                    return True
                except psycopg.errors.UniqueViolation:
                    return False

    async def unassign_supervisor(self, supervisor_id: str, technician_id: str) -> bool:
        """Remove supervisor assignment from technician"""
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM supervisor_assignments
                    WHERE supervisor_id = %s AND technician_id = %s
                """, (supervisor_id, technician_id))
                conn.commit()
                return cur.rowcount > 0

    async def get_technician_supervisors(self, technician_id: str) -> List[Dict]:
        """Get all supervisors assigned to a technician"""
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT u.user_id, u.email, u.full_name, u.profile_picture_url,
                           u.phone, sa.assigned_at
                    FROM supervisor_assignments sa
                    JOIN users u ON sa.supervisor_id = u.user_id
                    WHERE sa.technician_id = %s AND u.is_active = true
                    ORDER BY u.full_name
                """, (technician_id,))

                supervisors = cur.fetchall()

                return [
                    {
                        'user_id': supervisor[0],
                        'email': supervisor[1],
                        'full_name': supervisor[2],
                        'profile_picture_url': supervisor[3],
                        'phone': supervisor[4],
                        'assigned_at': supervisor[5].isoformat() if supervisor[5] else None
                    }
                    for supervisor in supervisors
                ]

    async def get_supervisor_technicians(self, supervisor_id: str) -> List[Dict]:
        """Get all technicians assigned to a supervisor"""
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT u.user_id, u.email, u.full_name, u.profile_picture_url,
                           u.phone, sa.assigned_at
                    FROM supervisor_assignments sa
                    JOIN users u ON sa.technician_id = u.user_id
                    WHERE sa.supervisor_id = %s AND u.is_active = true
                    ORDER BY u.full_name
                """, (supervisor_id,))

                technicians = cur.fetchall()

                return [
                    {
                        'user_id': tech[0],
                        'email': tech[1],
                        'full_name': tech[2],
                        'profile_picture_url': tech[3],
                        'phone': tech[4],
                        'assigned_at': tech[5].isoformat() if tech[5] else None
                    }
                    for tech in technicians
                ]


# Global instance
_user_service = None


def get_user_service() -> UserService:
    """Get or create user service instance"""
    global _user_service
    if _user_service is None:
        _user_service = UserService()
    return _user_service
