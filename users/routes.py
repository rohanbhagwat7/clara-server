"""User and team management API routes"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict
from users.service import get_user_service, UserService
from auth.service import get_auth_service, AuthService

router = APIRouter()


# ==================== REQUEST/RESPONSE MODELS ====================

class UpdateRoleRequest(BaseModel):
    role: str


class CreateTeamRequest(BaseModel):
    name: str
    settings: Optional[Dict] = None


class AddTeamMemberRequest(BaseModel):
    user_id: str
    role: str = 'member'


class AssignSupervisorRequest(BaseModel):
    supervisor_id: str
    technician_id: str


# ==================== DEPENDENCY: Get current user ====================

async def get_current_user(
    authorization: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Extract and validate user from JWT token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = authorization.replace("Bearer ", "")
    payload = auth_service.verify_access_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get('sub')
    user = auth_service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


# ==================== USER MANAGEMENT ENDPOINTS ====================

@router.get("/users")
async def get_all_users(
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Get all users (admin only)"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")

    users = await user_service.get_all_users()
    return {"users": users}


@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Get user details"""
    # Users can view their own profile, admins/supervisors can view anyone
    if current_user['user_id'] != user_id and current_user['role'] not in ['admin', 'supervisor']:
        raise HTTPException(status_code=403, detail="Access denied")

    user = await user_service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    request: UpdateRoleRequest,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Update user role (admin only)"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        success = await user_service.update_user_role(user_id, request.role)

        if not success:
            raise HTTPException(status_code=404, detail="User not found")

        return {"success": True, "user_id": user_id, "new_role": request.role}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users/role/technicians")
async def get_technicians(
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Get all technicians"""
    # Supervisors and admins can view technicians
    if current_user['role'] not in ['admin', 'supervisor']:
        raise HTTPException(status_code=403, detail="Supervisor or admin access required")

    technicians = await user_service.get_technicians()
    return {"technicians": technicians}


@router.get("/users/role/supervisors")
async def get_supervisors(
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Get all supervisors (admin only)"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")

    supervisors = await user_service.get_supervisors()
    return {"supervisors": supervisors}


# ==================== TEAM MANAGEMENT ENDPOINTS ====================

@router.get("/teams")
async def get_all_teams(
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Get all teams"""
    # Admins and supervisors can view teams
    if current_user['role'] not in ['admin', 'supervisor']:
        raise HTTPException(status_code=403, detail="Supervisor or admin access required")

    teams = await user_service.get_all_teams()
    return {"teams": teams}


@router.post("/teams")
async def create_team(
    request: CreateTeamRequest,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Create a new team (admin only)"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")

    team = await user_service.create_team(request.name, request.settings)
    return team


@router.get("/teams/{team_id}/members")
async def get_team_members(
    team_id: str,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Get team members"""
    # Admins and supervisors can view team members
    if current_user['role'] not in ['admin', 'supervisor']:
        raise HTTPException(status_code=403, detail="Supervisor or admin access required")

    members = await user_service.get_team_members(team_id)
    return {"members": members}


@router.post("/teams/{team_id}/members")
async def add_team_member(
    team_id: str,
    request: AddTeamMemberRequest,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Add member to team (admin only)"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        success = await user_service.add_team_member(team_id, request.user_id, request.role)

        if not success:
            raise HTTPException(status_code=400, detail="User is already a member of this team")

        return {"success": True, "team_id": team_id, "user_id": request.user_id}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/teams/{team_id}/members/{user_id}")
async def remove_team_member(
    team_id: str,
    user_id: str,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Remove member from team (admin only)"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")

    success = await user_service.remove_team_member(team_id, user_id)

    if not success:
        raise HTTPException(status_code=404, detail="User not found in team")

    return {"success": True, "team_id": team_id, "user_id": user_id}


# ==================== SUPERVISOR ASSIGNMENT ENDPOINTS ====================

@router.post("/supervisor-assignments")
async def assign_supervisor(
    request: AssignSupervisorRequest,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Assign supervisor to technician (admin only)"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")

    success = await user_service.assign_supervisor(
        request.supervisor_id,
        request.technician_id
    )

    if not success:
        raise HTTPException(
            status_code=400,
            detail="Supervisor already assigned to this technician"
        )

    return {
        "success": True,
        "supervisor_id": request.supervisor_id,
        "technician_id": request.technician_id
    }


@router.delete("/supervisor-assignments/{supervisor_id}/{technician_id}")
async def unassign_supervisor(
    supervisor_id: str,
    technician_id: str,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Remove supervisor assignment (admin only)"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")

    success = await user_service.unassign_supervisor(supervisor_id, technician_id)

    if not success:
        raise HTTPException(status_code=404, detail="Assignment not found")

    return {
        "success": True,
        "supervisor_id": supervisor_id,
        "technician_id": technician_id
    }


@router.get("/technicians/{technician_id}/supervisors")
async def get_technician_supervisors(
    technician_id: str,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Get supervisors assigned to a technician"""
    # Users can view their own supervisors, admins can view anyone's
    if current_user['user_id'] != technician_id and current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")

    supervisors = await user_service.get_technician_supervisors(technician_id)
    return {"supervisors": supervisors}


@router.get("/supervisors/{supervisor_id}/technicians")
async def get_supervisor_technicians(
    supervisor_id: str,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Get technicians assigned to a supervisor"""
    # Supervisors can view their own technicians, admins can view anyone's
    if current_user['user_id'] != supervisor_id and current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")

    technicians = await user_service.get_supervisor_technicians(supervisor_id)
    return {"technicians": technicians}
