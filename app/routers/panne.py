from fastapi import FastAPI,Response, status, HTTPException, Depends,Query, APIRouter
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func
from typing import List, Optional,Dict
from pydantic import BaseModel
from .. import models ,schemas,oauth2,utils
from ..database import  get_db

router = APIRouter(
    prefix="/panne",
    tags=["Panne"],
    # dependencies=[Depends(get_current_active_user)] # Uncomment for global auth
)

@router.post("/", response_model=schemas.PanneOut, status_code=status.HTTP_201_CREATED)
def create_new_panne(
    panne: schemas.PanneCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(oauth2.get_current_user) # Replace models.user.User with your actual User model
):

    db_panne = models.Panne(**panne.model_dump())
    db.add(db_panne)
    db.commit()
    db.refresh(db_panne)
    return db_panne

@router.get("/", response_model=List[schemas.PanneOut])
def read_all_pannes(
    skip: int = 0,
    limit: int = Query(default=10, le=1000), # Increased limit example
    search: Optional[str] = None,
    vehicle_id: Optional[int] = None, # Filter by vehicle
    category_panne_id: Optional[int] = None, # Filter by category
    status_filter: Optional[str] = None, # Filter by status (e.g., "active", "resolved")
    db: Session = Depends(get_db),
    current_user: str = Depends(oauth2.get_current_user)
):
    query = db.query(models.Panne).options(
        joinedload(models.Panne.vehicle), # Eager load vehicle
        joinedload(models.Panne.category_panne) # Eager load category_panne
    ) # Eager load for potentially including in PanneOut

    if vehicle_id is not None:
        query = query.filter(models.Panne.vehicle_id == vehicle_id)
    if category_panne_id is not None:
        query = query.filter(models.Panne.category_panne_id == category_panne_id)
    if status_filter:
        query = query.filter(models.Panne.status == status_filter)

    if search:
        # Ensure models.vehicle.Vehicle and models.category_panne.CategoryPanne are imported
        # and relationships are set up in models.panne.Panne
        query = query.join(models.Vehicle, models.Panne.vehicle_id == models.Vehicle.id, isouter=True) \
                     .join(models.CategoryPanne, models.Panne.category_panne_id == models.CategoryPanne.id, isouter=True)

        search_term = f"%{search.lower()}%"
        query = query.filter(
            or_(
                models.Panne.description.ilike(search_term),
                models.Panne.status.ilike(search_term),
                models.Vehicle.plate_number.ilike(search_term), # Search by vehicle plate
                # Add other vehicle fields if needed, e.g., models.vehicle.Vehicle.make.ilike(search_term)
                models.CategoryPanne.category_panne.ilike(search_term) # Search by category name
            )
        )
    
    pannes = query.order_by(models.Panne.panne_date.desc()).offset(skip).limit(limit).all()
    return pannes

@router.get("/{panne_id}", response_model=schemas.PanneOut)
def read_single_panne(
    panne_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(oauth2.get_current_user)
):
    db_panne = db.query(models.Panne).options(
        joinedload(models.Panne.vehicle),
        joinedload(models.Panne.category_panne)
    ).filter(models.Panne.id == panne_id).first()

    if db_panne is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Panne not found")
    return db_panne

@router.put("/{panne_id}", response_model=schemas.PanneOut)
def update_existing_panne(
    panne_id: int,
    panne_update: schemas.PanneUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(oauth2.get_current_user)
):
    db_panne = db.query(models.Panne).filter(models.Panne.id == panne_id).first()
    if not db_panne:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Panne not found")

    # Optional: Validate foreign keys if they are being updated
    if panne_update.vehicle_id is not None:
        vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == panne_update.vehicle_id).first()
        if not vehicle:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Vehicle with id {panne_update.vehicle_id} not found for update")
    
    if panne_update.category_panne_id is not None:
        category = db.query(models.CategoryPanne).filter(models.CategoryPanne.id == panne_update.category_panne_id).first()
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Panne category with id {panne_update.category_panne_id} not found for update")


    update_data = panne_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_panne, key, value)
    
    db.add(db_panne)
    db.commit()
    db.refresh(db_panne)
    return db_panne

@router.delete("/{panne_id}", status_code=status.HTTP_204_NO_CONTENT) # Common to return 204 for delete
def delete_existing_panne(
    panne_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(oauth2.get_current_user)
):
    db_panne = db.query(models.Panne).filter(models.Panne.id == panne_id).first()
    if not db_panne:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Panne not found")
    
    db.delete(db_panne)
    db.commit()
    return # For 204, no response body is sent