# app/routers/fuel.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc # For ordering
from typing import List, Optional
from datetime import date as date_type, datetime # For potential date filtering

# Assuming your project structure is app/routers, app/models, app/schemas, app/database
from .. import models, schemas, oauth2
from ..database import get_db

router = APIRouter(
    prefix="/fuel",
    tags=['Fuel Records'],
    dependencies=[Depends(oauth2.get_current_user)] # Secure all endpoints in this router
)

@router.post("/", response_model=schemas.FuelOut, status_code=status.HTTP_201_CREATED)
def create_new_fuel_record(
    fuel_payload: schemas.FuelCreatePayload, # Client sends this payload (cost is omitted)
    db: Session = Depends(get_db)
):
    """
    Create a new fuel record.
    Client provides vehicle_id, fuel_type_id, quantity, and price_little.
    The 'cost' is automatically calculated by the server as quantity * price_little.
    """
    # Validate Vehicle existence
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == fuel_payload.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Vehicle with ID {fuel_payload.vehicle_id} not found.")

    # Validate FuelType existence
    fuel_type = db.query(models.FuelType).filter(models.FuelType.id == fuel_payload.fuel_type_id).first()
    if not fuel_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Fuel Type with ID {fuel_payload.fuel_type_id} not found.")

    # Validate quantity and price_little
    if fuel_payload.quantity <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Fuel quantity must be greater than zero.")
    if fuel_payload.price_little <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Price per unit (price_little) must be greater than zero.")

    # Calculate cost
    calculated_cost = round(fuel_payload.quantity * fuel_payload.price_little, 2)

    # Create the database model instance
    db_fuel_record = models.Fuel(
        vehicle_id=fuel_payload.vehicle_id,
        fuel_type_id=fuel_payload.fuel_type_id,
        quantity=fuel_payload.quantity,
        price_little=fuel_payload.price_little,
        cost=calculated_cost # Use the calculated cost
    )
    
    db.add(db_fuel_record)
    db.commit()
    db.refresh(db_fuel_record)
    return db_fuel_record # Will be serialized by schemas.FuelOut

@router.get("/{fuel_id}", response_model=schemas.FuelOut)
def read_fuel_record_by_id(
    fuel_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific fuel record by its ID.
    """
    db_fuel_record = db.query(models.Fuel).filter(models.Fuel.id == fuel_id).first()
    if db_fuel_record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fuel record not found")
    return db_fuel_record

@router.get("/", response_model=List[schemas.FuelOut])
def read_all_fuel_records(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    vehicle_id_filter: Optional[int] = Query(default=None, alias="vehicle_id", description="Filter by Vehicle ID"),
    fuel_type_id_filter: Optional[int] = Query(default=None, alias="fuel_type_id", description="Filter by Fuel Type ID"),
    date_after: Optional[date_type] = Query(default=None, description="Filter records created on or after this date (YYYY-MM-DD)"),
    date_before: Optional[date_type] = Query(default=None, description="Filter records created on or before this date (YYYY-MM-DD)")
):
    """
    Retrieve a list of fuel records with optional filtering and pagination.
    """
    query = db.query(models.Fuel)

    if vehicle_id_filter is not None:
        query = query.filter(models.Fuel.vehicle_id == vehicle_id_filter)
    if fuel_type_id_filter is not None:
        query = query.filter(models.Fuel.fuel_type_id == fuel_type_id_filter)
    if date_after:
        query = query.filter(models.Fuel.created_at >= datetime.combine(date_after, datetime.min.time()))
    if date_before:
        query = query.filter(models.Fuel.created_at <= datetime.combine(date_before, datetime.max.time()))
    
    # Add relationship loading for eager loading if you frequently access related vehicle/fuel_type details
    # from sqlalchemy.orm import joinedload
    # query = query.options(joinedload(models.Fuel.vehicle_ref), joinedload(models.Fuel.fuel_type_ref))


    fuel_records = query.order_by(desc(models.Fuel.created_at)).offset(skip).limit(limit).all()
    return fuel_records

@router.put("/{fuel_id}", response_model=schemas.FuelOut)
def update_existing_fuel_record(
    fuel_id: int,
    fuel_payload: schemas.FuelUpdatePayload, # Client sends this payload for partial updates
    db: Session = Depends(get_db)
):
    """
    Update an existing fuel record.
    Client can provide vehicle_id, fuel_type_id, quantity, and/or price_little.
    If quantity or price_little are updated, 'cost' will be automatically recalculated.
    """
    db_fuel_record = db.query(models.Fuel).filter(models.Fuel.id == fuel_id).first()
    if not db_fuel_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fuel record not found for update")

    update_data = fuel_payload.model_dump(exclude_unset=True) # Get only fields sent by client

    # --- Validate foreign keys if they are being changed ---
    if "vehicle_id" in update_data and update_data["vehicle_id"] != db_fuel_record.vehicle_id:
        vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == update_data["vehicle_id"]).first()
        if not vehicle:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"New vehicle with ID {update_data['vehicle_id']} not found.")
    
    if "fuel_type_id" in update_data and update_data["fuel_type_id"] != db_fuel_record.fuel_type_id:
        fuel_type = db.query(models.FuelType).filter(models.FuelType.id == update_data["fuel_type_id"]).first()
        if not fuel_type:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"New Fuel Type with ID {update_data['fuel_type_id']} not found.")

    # --- Recalculate cost if quantity or price_little is updated ---
    recalculate_cost_flag = False
    # Start with current values from DB, then update if payload provides new values
    effective_quantity = db_fuel_record.quantity
    effective_price_little = db_fuel_record.price_little

    if "quantity" in update_data:
        if update_data["quantity"] <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fuel quantity must be greater than zero.")
        effective_quantity = update_data["quantity"]
        recalculate_cost_flag = True
    
    if "price_little" in update_data:
        if update_data["price_little"] <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Price per unit must be greater than zero.")
        effective_price_little = update_data["price_little"]
        recalculate_cost_flag = True

    if recalculate_cost_flag:
        # Ensure 'cost' is part of update_data so setattr applies it
        update_data['cost'] = round(effective_quantity * effective_price_little, 2)
    
    # Apply all changes from update_data to the database model instance
    for key, value in update_data.items():
        setattr(db_fuel_record, key, value)

    db.commit()
    db.refresh(db_fuel_record)
    return db_fuel_record

@router.delete("/{fuel_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_fuel_record(
    fuel_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a fuel record by its ID.
    """
    db_fuel_record = db.query(models.Fuel).filter(models.Fuel.id == fuel_id).first()
    if db_fuel_record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fuel record not found for deletion")

    db.delete(db_fuel_record)
    db.commit()
    return # No response body for 204 status