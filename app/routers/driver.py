# app/routers/driver.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_ # For search queries
from typing import List, Optional

from .. import models, schemas, oauth2 # Assuming your models, schemas, oauth2 are in these parent modules
from ..database import get_db # Assuming get_db is in the parent database module

router = APIRouter(
    prefix="/driver",  # All routes in this router will start with /driver
    tags=['Drivers'],    # Tag for Swagger UI documentation
    dependencies=[Depends(oauth2.get_current_user)] # Apply authentication to all driver routes
)

@router.post("/", response_model=schemas.DriverOut, status_code=status.HTTP_201_CREATED)
def create_new_driver(
    driver_payload: schemas.DriverCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new driver.
    Requires: last_name, first_name, cni_number, email, matricule.
    CNI, Email, and Matricule must be unique.
    """
    # Check for uniqueness of cni_number, email, and matricule
    existing_driver_cni = db.query(models.Driver).filter(models.Driver.cni_number == driver_payload.cni_number).first()
    if existing_driver_cni:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Driver with CNI number '{driver_payload.cni_number}' already exists.")

    existing_driver_email = db.query(models.Driver).filter(models.Driver.email == driver_payload.email).first()
    if existing_driver_email:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Driver with email '{driver_payload.email}' already exists.")

    existing_driver_matricule = db.query(models.Driver).filter(models.Driver.matricule == driver_payload.matricule).first()
    if existing_driver_matricule:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Driver with matricule '{driver_payload.matricule}' already exists.")

    db_driver = models.Driver(**driver_payload.model_dump())
    db.add(db_driver)
    db.commit()
    db.refresh(db_driver)
    return db_driver

@router.get("/{driver_id}", response_model=schemas.DriverOut)
def read_driver_by_id(
    driver_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific driver by their ID.
    """
    db_driver = db.query(models.Driver).filter(models.Driver.id == driver_id).first()
    if db_driver is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    return db_driver

@router.get("/", response_model=List[schemas.DriverOut])
def read_all_drivers(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = Query(default=100, ge=1, le=1000),
    search: Optional[str] = Query(default=None, description="Search term for name, CNI, email, or matricule")
):
    """
    Retrieve a list of drivers.
    Supports pagination (`skip`, `limit`) and an optional `search` term.
    """
    query = db.query(models.Driver)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                models.Driver.first_name.ilike(search_term),
                models.Driver.last_name.ilike(search_term),
                (models.Driver.first_name + " " + models.Driver.last_name).ilike(search_term), # Search full name
                models.Driver.cni_number.ilike(search_term),
                models.Driver.email.ilike(search_term),
                models.Driver.matricule.ilike(search_term)
            )
        )

    drivers = query.order_by(models.Driver.last_name, models.Driver.first_name).offset(skip).limit(limit).all()
    return drivers

@router.put("/{driver_id}", response_model=schemas.DriverOut)
def update_existing_driver(
    driver_id: int,
    driver_payload: schemas.DriverCreate, # Using DriverCreate as it has all required fields for update
                                          # If partial updates are needed, create a DriverUpdate schema
    db: Session = Depends(get_db)
):
    """
    Update an existing driver by their ID.
    All fields (last_name, first_name, cni_number, email, matricule) are expected.
    If you need partial updates, create a `DriverUpdate(BaseModel)` schema with Optional fields.
    """
    db_driver = db.query(models.Driver).filter(models.Driver.id == driver_id).first()
    if not db_driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found for update")

    update_data = driver_payload.model_dump(exclude_unset=False) # Get all fields from payload

    # Check for uniqueness if sensitive fields are changed
    if 'cni_number' in update_data and update_data['cni_number'] != db_driver.cni_number:
        existing_cni = db.query(models.Driver).filter(models.Driver.cni_number == update_data['cni_number']).first()
        if existing_cni:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"CNI number '{update_data['cni_number']}' already in use.")
    
    if 'email' in update_data and update_data['email'] != db_driver.email:
        existing_email = db.query(models.Driver).filter(models.Driver.email == update_data['email']).first()
        if existing_email:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Email '{update_data['email']}' already in use.")

    if 'matricule' in update_data and update_data['matricule'] != db_driver.matricule:
        existing_matricule = db.query(models.Driver).filter(models.Driver.matricule == update_data['matricule']).first()
        if existing_matricule:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Matricule '{update_data['matricule']}' already in use.")

    for key, value in update_data.items():
        setattr(db_driver, key, value)

    db.commit()
    db.refresh(db_driver)
    return db_driver

@router.delete("/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_driver(
    driver_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a driver by their ID.
    """
    db_driver = db.query(models.Driver).filter(models.Driver.id == driver_id).first()
    if db_driver is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found for deletion")

    # Optional: Check if driver is assigned to any active trips before deletion
    # active_trips = db.query(models.Trip).filter(models.Trip.driver_id == driver_id, models.Trip.status.notin_(['completed', 'cancelled'])).first()
    # if active_trips:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
    #                         detail="Cannot delete driver. Driver is assigned to active or planned trips.")

    db.delete(db_driver)
    db.commit()
    return # No content to return for 204