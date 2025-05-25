from fastapi import FastAPI,Response, status, HTTPException, Depends, APIRouter
from typing import Optional,List, Dict 
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from .. import models ,schemas,oauth2,utils
from ..database import  get_db

router = APIRouter(prefix="/vehicle_type", tags=['Vehicle Type'])

############################################################################################################################
@router.post("/",status_code=status.HTTP_201_CREATED, response_model=schemas.VehicleTypeOut) 
def create_veh_type(veh_type : schemas.VehicleTypeCreate, db:Session = Depends(get_db)):
  
    
    new_veh_type = models.VehicleType(**veh_type.dict())
    db.add(new_veh_type)
    db.commit()
    db.refresh(new_veh_type)
    return new_veh_type

############################################################################################################################

@router.get("/", response_model = List[schemas.VehicleTypeOut])
def get_vehicle_types(db:Session = Depends(get_db),limit : int = 10, skip : int = 0, search :Optional[str] = ""):
              
  
    ##filter all vehicle types at the same time
    veh_types = db.query(models.VehicleType).filter(models.VehicleType.vehicle_type.contains(search)).limit(limit).offset(skip).all()
    return veh_types
############################################################################################################################

@router.get("/{id}", response_model=schemas.VehicleTypeOut)
def get_veh_type(id : int, db :Session = Depends(get_db),  current_user : str = Depends(oauth2.get_current_user)):
    veh_type = db.query(models.VehicleType).filter(models.VehicleType.id == id).first()
    
    if not veh_type :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Vehicle Type with id : {id} was not found")
    return veh_type

#############################################################################################################################

@router.delete("/{id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_veh_type(id:int,db:Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
   
   veh_type_query = db.query(models.VehicleType).filter(models.VehicleType.id == id)
   veh_type = veh_type_query.first()
   
   if veh_type == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Vehicle Type with id: {id} does not exist")
  
         
   veh_type_query.delete(synchronize_session = False) 
   db.commit()  
   return Response(status_code=status.HTTP_204_NO_CONTENT)
############################################################################################################################

@router.put("/{id}", response_model=schemas.VehicleTypeCreate)
def update_veh_type(id:int,updated_veh_type:schemas.VehicleTypeCreate,db:Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
  
    veh_type_query = db.query(models.VehicleType).filter(models.VehicleType.id == id)
    veh_type =veh_type_query.first()
    if veh_type == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Vehicle Type with id: {id} does not exist")
   
    veh_type_query.update(updated_veh_type.dict(),synchronize_session = False)
    db.commit()
    return veh_type_query.first()  
############################################################################################################################