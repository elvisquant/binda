# routers/user.py
from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter, Request
from typing import Optional, List
from sqlalchemy.orm import Session
from .. import models, schemas, oauth2, utils # Your existing imports
from ..database import get_db
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/user", tags=['User'])
templates = Jinja2Templates(directory="app/templates") # Ensure this path is correct

# CREATE USER
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.UserOut)
def create_user(user_create_data: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user_by_email = db.query(models.User).filter(models.User.email == user_create_data.email).first()
    if existing_user_by_email:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    existing_user_by_username = db.query(models.User).filter(models.User.username == user_create_data.username).first()
    if existing_user_by_username:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")

    hashed_password = utils.hash(user_create_data.password)
    
    # Create a dictionary from user_create_data, then update password
    user_data_dict = user_create_data.dict()
    user_data_dict["password"] = hashed_password # Replace plain password with hashed
    
    new_user = models.User(**user_data_dict) # This now uses the 'status' from UserCreate
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# GET ALL USERS (API)
@router.get("/", response_model=List[schemas.UserOut])
def get_users_api( # Renamed to avoid conflict if you have another get_users
    db: Session = Depends(get_db),
    current_api_user: schemas.UserOut = Depends(oauth2.get_current_user), # Make sure get_current_user returns a user model/schema
    limit: int = 100, # Increased default limit
    skip: int = 0,
    search: Optional[str] = ""
):
    query = db.query(models.User)
    if search:
        query = query.filter(models.User.email.contains(search)) # Or search by username too
    
    users = query.order_by(models.User.id).limit(limit).offset(skip).all()
    return users

# GET USERS HTML PAGE
@router.get("/users-page", response_class=HTMLResponse)
async def get_users_page_view( # Renamed to avoid conflict
    request: Request,
    db: Session = Depends(get_db) # Keep if needed for initial data, but JS will fetch
):
    user_info_for_template = None
    try:
        current_user_data = await oauth2.get_current_user_optional(request) # Made-up function for optional user
        if current_user_data:
            user_info_for_template = {"username": current_user_data.username} # Example
    except HTTPException:
        pass

    return templates.TemplateResponse("users.html", {
        "request": request,
        "current_user_info": user_info_for_template # Pass minimal info or None
    })

# GET SPECIFIC USER BY ID
@router.get("/{id}", response_model=schemas.UserOut)
def get_user_by_id( # Renamed
    id: int,
    db: Session = Depends(get_db),
    current_api_user: schemas.UserOut = Depends(oauth2.get_current_user)
):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id: {id} was not found"
        )
    return user

# DELETE USER
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_by_id( # Renamed
    id: int,
    db: Session = Depends(get_db),
    current_api_user: schemas.UserOut = Depends(oauth2.get_current_user)
):
    user_query = db.query(models.User).filter(models.User.id == id)
    user_to_delete = user_query.first()
    if user_to_delete is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id: {id} does not exist"
        )
    user_query.delete(synchronize_session=False) 
    db.commit()  
    return Response(status_code=status.HTTP_204_NO_CONTENT) # FastAPI handles this correctly

# UPDATE USER
@router.put("/{id}", response_model=schemas.UserOut)
def update_user_by_id( # Renamed
    id: int,
    user_update_payload: schemas.UserUpdate, # <<< CRITICAL CHANGE: Use UserUpdate
    db: Session = Depends(get_db),
    current_api_user: schemas.UserOut = Depends(oauth2.get_current_user)
):
    user_query = db.query(models.User).filter(models.User.id == id)
    db_user_to_update = user_query.first()
    
    if db_user_to_update is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id: {id} does not exist"
        )
   
    update_data_dict = user_update_payload.dict(exclude_unset=True) # Get only fields that were actually sent

    if "username" in update_data_dict and update_data_dict["username"] != db_user_to_update.username:
        existing_user_by_username = db.query(models.User).filter(models.User.username == update_data_dict["username"]).first()
        if existing_user_by_username:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")
            
    if "email" in update_data_dict and update_data_dict["email"] != db_user_to_update.email:
        existing_user_by_email = db.query(models.User).filter(models.User.email == update_data_dict["email"]).first()
        if existing_user_by_email:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user_query.update(update_data_dict, synchronize_session=False)
    db.commit()
    db.refresh(db_user_to_update) # Refresh the instance you fetched
    return db_user_to_update