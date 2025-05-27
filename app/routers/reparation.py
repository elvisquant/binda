# reparation.py

from fastapi import APIRouter, HTTPException, Depends, status, Query, Response
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func
from typing import List, Optional
import datetime # For date filtering

# Assuming your project structure has these in the parent directory (e.g., app/)
# and they are correctly defined:
from .. import models
from .. import schemas
from .. import oauth2
from ..database import get_db

router = APIRouter(
    prefix="/reparation",
    tags=["Reparation"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.ReparationResponse, status_code=status.HTTP_201_CREATED)
def create_reparation(
    reparation_in: schemas.ReparationCreate,
    db: Session = Depends(get_db),
    current_user: schemas.UserOut = Depends(oauth2.get_current_user) # Ensure UserOut schema matches what get_current_user returns
):
    # Validate foreign key existence
    panne_exists = db.query(models.Panne).filter(models.Panne.id == reparation_in.panne_id).first()
    if not panne_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Panne with id {reparation_in.panne_id} not found")

    garage_exists = db.query(models.Garage).filter(models.Garage.id == reparation_in.garage_id).first()
    if not garage_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Garage with id {reparation_in.garage_id} not found")

    reparation_data = reparation_in.model_dump()
    if reparation_data.get("status") and isinstance(reparation_data["status"], schemas.ReparationStatusEnum):
        reparation_data["status"] = reparation_data["status"].value

    # Example: If you want to associate the user who created the reparation
    # Ensure 'created_by_user_id' field exists in your models.Reparation
    # if hasattr(models.Reparation, 'created_by_user_id'):
    #     reparation_data['created_by_user_id'] = current_user.id

    db_reparation = models.Reparation(**reparation_data)
    db.add(db_reparation)
    db.commit()
    db.refresh(db_reparation)
    # The returned db_reparation will be automatically converted to schemas.ReparationResponse
    # including nested 'panne' and 'garage' objects if eager loaded and defined in the schema.
    return db_reparation

@router.get("/{reparation_id}", response_model=schemas.ReparationResponse)
def read_reparation(
    reparation_id: int,
    db: Session = Depends(get_db),
    #current_user: schemas.UserOut = Depends(oauth2.get_current_user)
):
    db_reparation = db.query(models.Reparation).options(
        joinedload(models.Reparation.panne),  # Eager loads the related Panne object
        joinedload(models.Reparation.garage) # Eager loads the related Garage object
    ).filter(models.Reparation.id == reparation_id).first()

    if db_reparation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reparation not found")
    return db_reparation

@router.get("/", response_model=List[schemas.ReparationResponse])
def read_reparations(
    skip: int = 0,
    limit: int = Query(default=10, le=200),
    search: Optional[str] = None,
    panne_id_filter: Optional[int] = None,
    garage_id_filter: Optional[int] = None,
    status_filter: Optional[schemas.ReparationStatusEnum] = None,
    start_date: Optional[datetime.date] = None, # For filtering repair_date
    end_date: Optional[datetime.date] = None,     # For filtering repair_date
    db: Session = Depends(get_db),
    current_user: schemas.UserOut = Depends(oauth2.get_current_user)
):
    query = db.query(models.Reparation).options(
        joinedload(models.Reparation.panne), # Eager load for response and potential search
        joinedload(models.Reparation.garage) # Eager load for response and potential search
    )

    if panne_id_filter is not None:
        query = query.filter(models.Reparation.panne_id == panne_id_filter)
    if garage_id_filter is not None:
        query = query.filter(models.Reparation.garage_id == garage_id_filter)
    if status_filter:
        query = query.filter(models.Reparation.status == status_filter.value)

    if start_date:
        query = query.filter(models.Reparation.repair_date >= datetime.datetime.combine(start_date, datetime.time.min))
    if end_date:
        query = query.filter(models.Reparation.repair_date <= datetime.datetime.combine(end_date, datetime.time.max))

    if search:
        search_term = f"%{search.lower()}%"
        # Ensure models.Panne has 'description' and models.Garage has 'nom_garage' for these search conditions.
        # outerjoin is used so reparations are still returned if related Panne/Garage doesn't match search but other fields do.
        query = query.outerjoin(models.Panne, models.Reparation.panne_id == models.Panne.id) \
                     .outerjoin(models.Garage, models.Reparation.garage_id == models.Garage.id)

        query = query.filter(
            or_(
                models.Reparation.receipt.ilike(search_term),
                models.Reparation.status.ilike(search_term),
                func.cast(models.Reparation.cost, models.String).ilike(search_term), # Cast cost to string for ilike
                models.Panne.description.ilike(search_term),
                models.Garage.nom_garage.ilike(search_term)
            )
        )

    reparations = query.order_by(models.Reparation.repair_date.desc()).offset(skip).limit(limit).all()
    return reparations

@router.put("/{reparation_id}", response_model=schemas.ReparationResponse)
def update_reparation(
    reparation_id: int,
    reparation_in: schemas.ReparationUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.UserOut = Depends(oauth2.get_current_user)
):
    db_reparation = db.query(models.Reparation).filter(models.Reparation.id == reparation_id).first()
    if db_reparation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reparation not found")

    update_data = reparation_in.model_dump(exclude_unset=True) # Only update fields that were actually sent

    # Validate foreign keys if they are being updated
    if "panne_id" in update_data and update_data["panne_id"] is not None:
        if not db.query(models.Panne).filter(models.Panne.id == update_data["panne_id"]).first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Panne with id {update_data['panne_id']} not found")
    if "garage_id" in update_data and update_data["garage_id"] is not None:
        if not db.query(models.Garage).filter(models.Garage.id == update_data["garage_id"]).first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Garage with id {update_data['garage_id']} not found")

    for key, value in update_data.items():
        if key == "status" and isinstance(value, schemas.ReparationStatusEnum):
            setattr(db_reparation, key, value.value)
        elif value is not None: # Only set attribute if value from Pydantic model is not None (respecting exclude_unset)
            setattr(db_reparation, key, value)
        # If value is None and the field is nullable in DB, and you want to explicitly set it to NULL,
        # you might remove 'elif value is not None' and let setattr(db_reparation, key, None) happen.
        # However, with exclude_unset=True, None values that were not part of the request won't be in update_data.
        # If a field *was* in the request as null, it would be in update_data as None.

    db.commit()
    db.refresh(db_reparation)
    return db_reparation

@router.delete("/{reparation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reparation(
    reparation_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserOut = Depends(oauth2.get_current_user)
):
    db_reparation = db.query(models.Reparation).filter(models.Reparation.id == reparation_id).first()
    if db_reparation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reparation not found")

    # Optional: Implement ownership check before deletion
    # e.g., if hasattr(db_reparation, 'created_by_user_id') and db_reparation.created_by_user_id != current_user.id:
    #     if not getattr(current_user, 'is_admin', False): # Assuming UserOut has an is_admin field
    #         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this reparation")

    db.delete(db_reparation)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)



