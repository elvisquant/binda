from fastapi import Response, status, HTTPException, Depends, APIRouter
from typing import Optional,List
from sqlalchemy.orm import Session
from sqlalchemy import func
from .. import models ,schemas,oauth2
from sqlalchemy import or_, func # Added func for potential casting if needed
from ..database import  get_db

router = APIRouter(prefix="/maintenance", tags=['Maintenance'])

############################################################################################################################
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.MaintenanceOut)
def create_maintenance(
    maintenance: schemas.MaintenanceCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user) # Corrected type hint
):
    # You could add logic here using current_user if needed, e.g., logging who created it
    # or associating the maintenance record with the current_user if your model supports it.

    new_maintenance = models.Maintenance(**maintenance.model_dump()) # Pydantic V2
    # new_maintenance = models.Maintenance(**maintenance.dict()) # Pydantic V1
    db.add(new_maintenance)
    db.commit()
    db.refresh(new_maintenance)
    return new_maintenance

############################################################################################################################

@router.get("/", response_model=List[schemas.MaintenanceOut])
def get_maintenance_logs( # Renamed for clarity (plural)
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user), # Corrected type hint
    limit: int = 10,  # A more reasonable default limit
    skip: int = 0,
    search: Optional[str] = ""
):
    query = db.query(models.Maintenance)

    if search:
        search_term = f"%{search.lower()}%"
        # Ensure related models are imported if not already at the top
        # from ..models import Vehicle, CategoryMaintenance, Garage # Example

        # Join with related tables for searching
        # Using isouter=True to still get maintenance records if a related entity is somehow missing
        # (though with FK constraints, this shouldn't happen for non-nullable FKs)
        query = query.join(models.Vehicle, models.Maintenance.vehicule_id == models.Vehicle.id, isouter=True) \
                     .join(models.CategoryMaintenance, models.Maintenance.cat_maintenance_id == models.CategoryMaintenance.id, isouter=True) \
                     .join(models.Garage, models.Maintenance.garage_id == models.Garage.id, isouter=True)

        query = query.filter(
            or_(
                models.Maintenance.receipt.ilike(search_term),
                models.Vehicle.plate_number.ilike(search_term), # Assumes Vehicle model has plate_number
                models.CategoryMaintenance.cat_maintenance.ilike(search_term), # Assumes CategoryMaintenance model has cat_maintenance
                models.Garage.nom_garage.ilike(search_term), # Assumes Garage model has nom_garage
                # To search by ID if `search` is a number (optional):
                # func.cast(models.Maintenance.id, String).ilike(search_term),
                # func.cast(models.Maintenance.maintenance_cost, String).ilike(search_term) # For searching cost as string
            )
        )

    # Order results for consistent pagination
    maintenances = query.order_by(models.Maintenance.maintenance_date.desc()).limit(limit).offset(skip).all()
    return maintenances

############################################################################################################################

@router.get("/{id}", response_model=schemas.MaintenanceOut) # Corrected response_model
def get_maintenance_log_by_id( # Renamed for clarity
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user) # Corrected type hint
):
    maintenance = db.query(models.Maintenance).filter(models.Maintenance.id == id).first()

    if not maintenance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Maintenance log with id: {id} was not found"
        )
    return maintenance

#############################################################################################################################

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_maintenance(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user) # Corrected type hint
):
    maintenance_query = db.query(models.Maintenance).filter(models.Maintenance.id == id)
    maintenance_to_delete = maintenance_query.first()

    if maintenance_to_delete is None: # Use 'is None'
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Maintenance log with id: {id} does not exist"
        )

    # Add authorization logic here if needed:
    # e.g., if current_user.id != maintenance_to_delete.creator_id and not current_user.is_admin:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to perform requested action")

    maintenance_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

############################################################################################################################

@router.put("/{id}", response_model=schemas.MaintenanceOut) # Recommended: Return MaintenanceOut
def update_maintenance(
    id: int,
    maintenance_update_data: schemas.MaintenanceCreate, # Input data
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user) # Corrected type hint
):
    maintenance_query = db.query(models.Maintenance).filter(models.Maintenance.id == id)
    existing_maintenance = maintenance_query.first()

    if existing_maintenance is None: # Use 'is None'
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Maintenance log with id: {id} does not exist"
        )

    # Add authorization logic here if needed

    # Pydantic V2: .model_dump()
    # For PUT, typically all required fields are provided.
    # If you want PATCH-like behavior (partial updates), use exclude_unset=True
    update_data = maintenance_update_data.model_dump(exclude_unset=False)
    # Pydantic V1: .dict()
    # update_data = maintenance_update_data.dict(exclude_unset=False)

    maintenance_query.update(update_data, synchronize_session=False)
    db.commit()
    db.refresh(existing_maintenance) # Refresh the instance to get DB-generated/updated values
    return existing_maintenance