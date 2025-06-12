from fastapi import FastAPI,Response, status, HTTPException, Depends, APIRouter
from typing import Optional,List, Dict 
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from .. import models ,schemas,oauth2,utils
from ..database import  get_db

router = APIRouter(prefix="/vehicle", tags=['Vehicle'])

############################################################################################################################
@router.post("/",status_code=status.HTTP_201_CREATED, response_model=schemas.VehicleOut) 
def create_vehicle(vehicle : schemas.VehicleCreate, db:Session = Depends(get_db)):
    
    
    new_vehicle = models.Vehicle(**vehicle.dict())
    db.add(new_vehicle)
    db.commit()
    db.refresh(new_vehicle)
    return new_vehicle

############################################################################################################################

@router.get("/", response_model = List[schemas.VehicleOut])
def get_vehicles(db:Session = Depends(get_db),limit : int = 1000, skip : int = 0, search :Optional[str] = ""):
              
  
    ##filter all vehicles at the same time
    vehicles = db.query(models.Vehicle).filter(models.Vehicle.plate_number.contains(search)).limit(limit).offset(skip).all()
    return vehicles
############################################################################################################################

@router.get("/{id}", response_model=schemas.VehicleOut)
def get_vehicle(id : int, db :Session = Depends(get_db),  current_user : str = Depends(oauth2.get_current_user)):
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == id).first()
    
    if not vehicle :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"vehicle with id : {id} was not found")
    return vehicle

#############################################################################################################################

@router.delete("/{id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle(id:int,db:Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
   
   vehicle_query = db.query(models.Vehicle).filter(models.Vehicle.id == id)
   vehicle = vehicle_query.first()
   
   if vehicle == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Vehicle with id: {id} does not exist")
  
         
   vehicle_query.delete(synchronize_session = False) 
   db.commit()  
   return Response(status_code=status.HTTP_204_NO_CONTENT)
############################################################################################################################

@router.put("/{id}", response_model=schemas.VehicleCreate)
def update_vehicle(id:int,updated_vehicle:schemas.VehicleCreate,db:Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
  
    vehicle_query = db.query(models.Vehicle).filter(models.Vehicle.id == id)
    vehicle =vehicle_query.first()
    if vehicle == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Vehicle with id: {id} does not exist")
   
    vehicle_query.update(updated_vehicle.dict(),synchronize_session = False)
    db.commit()
    return vehicle_query.first()  
############################################################################################################################


@router.patch("/{id}/status", status_code=status.HTTP_204_NO_CONTENT)
def update_vehicle_status(id: int, status_update: schemas.VehicleStatusUpdate, db: Session = Depends(get_db)):
    """
    Update only the status of a specific vehicle.
    This is a more efficient and secure way to handle simple status changes.
    """
    vehicle_query = db.query(models.Vehicle).filter(models.Vehicle.id == id)
    vehicle = vehicle_query.first()

    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Vehicle with id {id} not found")

    # Update only the status field
    vehicle_query.update({"status": status_update.status}, synchronize_session=False)
    db.commit()

    # We return no content on success, as indicated by HTTP 204
    return
################################################################################################################################

