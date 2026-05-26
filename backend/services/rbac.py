"""
Role-Based Access Control (RBAC) for OmicsFlow.

Roles:
  - admin:          Full system access, manage users, sequencers, settings
  - bioinformatician: Run pipelines, manage tasks, view all projects
  - librarian:      Create projects, manage samples, upload data
  - viewer:         Read-only access to assigned projects
"""

from functools import wraps
from typing import List
from fastapi import HTTPException, status
from models.database import User

# Role hierarchy (higher index = more permissions)
ROLE_HIERARCHY = {
    "viewer": 0,
    "librarian": 1,
    "bioinformatician": 2,
    "admin": 3,
}

# Permission definitions
ROLE_PERMISSIONS = {
    "admin": {
        "users:read", "users:write", "users:delete",
        "projects:read", "projects:write", "projects:delete",
        "samples:read", "samples:write", "samples:delete",
        "datasets:read", "datasets:write", "datasets:delete",
        "pipelines:read", "pipelines:write", "pipelines:delete",
        "tasks:read", "tasks:write", "tasks:delete", "tasks:run",
        "sequencers:read", "sequencers:write", "sequencers:delete",
        "skills:read", "skills:write",
        "ai:read", "ai:write",
    },
    "bioinformatician": {
        "projects:read", "projects:write",
        "samples:read", "samples:write",
        "datasets:read", "datasets:write", "datasets:delete",
        "pipelines:read", "pipelines:write",
        "tasks:read", "tasks:write", "tasks:delete", "tasks:run",
        "sequencers:read",
        "skills:read",
        "ai:read", "ai:write",
    },
    "librarian": {
        "projects:read", "projects:write",
        "samples:read", "samples:write",
        "datasets:read", "datasets:write", "datasets:delete",
        "pipelines:read",
        "tasks:read",
        "sequencers:read",
        "skills:read",
    },
    "viewer": {
        "projects:read",
        "samples:read",
        "datasets:read",
        "pipelines:read",
        "tasks:read",
        "sequencers:read",
    },
}


def get_user_roles(user: User) -> List[str]:
    """Get effective roles for a user."""
    if user.is_superuser:
        return ["admin"]
    roles = user.roles or []
    if not roles:
        return ["viewer"]  # default role
    return roles


def has_permission(user: User, permission: str) -> bool:
    """Check if user has a specific permission."""
    if user.is_superuser:
        return True
    
    roles = get_user_roles(user)
    for role in roles:
        perms = ROLE_PERMISSIONS.get(role, set())
        if permission in perms:
            return True
    return False


def check_permission(user: User, permission: str):
    """Raise HTTP 403 if user lacks permission."""
    if not has_permission(user, permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied. Required: {permission}",
        )


def check_resource_access(user: User, resource_owner_id: str, permission: str):
    """Check resource-level access: own data or all data."""
    if has_permission(user, permission):
        return True
    if has_permission(user, permission + ":own") and str(user.id) == str(resource_owner_id):
        return True
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Access denied to this resource. Required: {permission}",
    )


def require_roles(*required_roles: str):
    """Decorator to require specific roles."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User = None, **kwargs):
            if current_user is None:
                # Try to extract from args/kwargs
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                        break
                if "current_user" in kwargs:
                    current_user = kwargs["current_user"]
            
            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )
            
            user_roles = get_user_roles(current_user)
            if not any(r in user_roles for r in required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"One of these roles required: {', '.join(required_roles)}",
                )
            
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator