# app/routers/admin_api.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import schemas, models, oauth2, database

router = APIRouter(
    prefix="/api/admin",  # All routes in this file will start with /api/admin
    tags=["Admin API"],
    dependencies=[Depends(oauth2.get_current_user)] # Apply auth to all routes in this router
)

@router.get("/me", response_model=schemas.UserOut) # Assuming UserResponse schema exists
async def get_admin_user_me(current_user: models.User = Depends(oauth2.get_current_user)):
    """
    Get details for the currently authenticated admin user.
    """
    # You might want to add a check here if only users with a specific role (e.g., 'admin')
    # can access this, even if they are authenticated.
    # For example: if "admin" not in current_user.roles: raise HTTPException(...)
    return current_user

@router.get("/data", response_model=dict)
async def get_admin_sensitive_data(current_user: models.User = Depends(oauth2.get_current_user)):
    """
    Example of a protected endpoint fetching sensitive admin data.
    """
    # Add role/permission check if necessary:
    # if not current_user.is_superuser: # or some other role check
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this resource")
    
    return {
        "message": f"Welcome, {current_user.username}! This is sensitive admin data.",
        "user_id": current_user.id,
        "email": current_user.email,
        "user_status_active": current_user.is_active,
        "data_points": [
            {"id": 1, "value": "Top Secret Info A"},
            {"id": 2, "value": "Confidential Report B"}
        ]
    }

@router.get("/users", response_model=List[schemas.UserOut]) # Example: List all users
async def list_all_users(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user) # Ensure admin is making this request
):
    # Add specific permission check, e.g., current_user must be a superuser
    # if not current_user.is_superuser:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")
    users = db.query(models.User).all()
    return users