from fastapi import FastAPI,Response, status, HTTPException, Depends, APIRouter
from typing import Optional,List, Dict 
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from .. import models ,schemas,oauth2,utils
from ..database import  get_db

router = APIRouter(prefix="/vehicle_transmission", tags=['Vehicle Transmission'])

############################################################################################################################
@router.post("/",status_code=status.HTTP_201_CREATED, response_model=schemas.VehicleTransmissionOut) 
def create_veh_transmission(veh_transmission : schemas.VehicleTransmissionCreate, db:Session = Depends(get_db)):

    
    new_veh_transmission = models.VehicleTransmission(**veh_transmission.dict())
    db.add(new_veh_transmission)
    db.commit()
    db.refresh(new_veh_transmission)
    return new_veh_transmission

############################################################################################################################

@router.get("/", response_model = List[schemas.VehicleTransmissionOut])
def get_vehicles_transmission(db:Session = Depends(get_db),limit : int = 10, skip : int = 0, search :Optional[str] = ""):
              
  
    ##filter all vehicles transmission at the same time
    veh_transmission = db.query(models.VehicleTransmission).filter(models.VehicleTransmission.vehicle_transmission.contains(search)).limit(limit).offset(skip).all()
    return veh_transmission 
############################################################################################################################

@router.get("/{id}", response_model=schemas.VehicleTransmissionOut)
def get_veh_transmission(id : int, db :Session = Depends(get_db),  current_user : str = Depends(oauth2.get_current_user)):
    veh_transmission = db.query(models.VehicleTransmission).filter(models.VehicleTransmission.id == id).first()
    
    if not veh_transmission :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Vehicle Transmission with id : {id} was not found")
    return veh_transmission

#############################################################################################################################

@router.delete("/{id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_veh_transmission(id:int,db:Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
   
   veh_transmission_query = db.query(models.VehicleTransmission).filter(models.VehicleTransmission.id == id)
   veh_transmission = veh_transmission_query.first()
   
   if veh_transmission == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Vehicle Transmission with id: {id} does not exist")
  
         
   veh_transmission_query.delete(synchronize_session = False) 
   db.commit()  
   return Response(status_code=status.HTTP_204_NO_CONTENT)
############################################################################################################################

@router.put("/{id}", response_model=schemas.VehicleTransmissionCreate)
def update_veh_transmission(id:int,updated_veh_transmission:schemas.VehicleTransmissionCreate,db:Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
  
    veh_transmission_query = db.query(models.VehicleTransmission).filter(models.VehicleTransmission.id == id)
    veh_transmission =veh_transmission_query.first()
    if veh_transmission == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Vehicle Transmission with id: {id} does not exist")
   
    veh_transmission_query.update(updated_veh_transmission.dict(),synchronize_session = False)
    db.commit()
    return veh_transmission_query.first()  
############################################################################################################################