from fastapi import FastAPI,Response, status, HTTPException, Depends, APIRouter
from typing import Optional,List, Dict 
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from .. import models ,schemas,oauth2,utils
from ..database import  get_db

router = APIRouter(prefix="/vehicle_make", tags=['Vehicle Make'])

############################################################################################################################
@router.post("/",status_code=status.HTTP_201_CREATED, response_model=schemas.VehicleMakeOut) 
def create_veh_make(veh_make : schemas.VehicleMakeCreate, db:Session = Depends(get_db)):
    
    
    new_veh_make = models.VehicleMake(**veh_make.dict())
    db.add(new_veh_make)
    db.commit()
    db.refresh(new_veh_make)
    return new_veh_make

############################################################################################################################

@router.get("/", response_model = List[schemas.VehicleMakeOut])
def get_vehicles_make(db:Session = Depends(get_db),limit : int = 10, skip : int = 0, search :Optional[str] = ""):
              
  
    ##filter all Vehicle Make at the same time
    vehicles_make= db.query(models.VehicleMake).filter(models.VehicleMake.vehicle_make.contains(search)).limit(limit).offset(skip).all()
    return vehicles_make 
############################################################################################################################

@router.get("/{id}", response_model=schemas.VehicleMakeOut)
def get_veh_make(id : int, db :Session = Depends(get_db),  current_user : str = Depends(oauth2.get_current_user)):
    veh_make = db.query(models.VehicleMake).filter(models.VehicleMake.id == id).first()
    
    if not veh_make :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Vehicle Make with id : {id} was not found")
    return veh_make

#############################################################################################################################

@router.delete("/{id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_veh_make(id:int,db:Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
   
   veh_make_query = db.query(models.VehicleMake).filter(models.VehicleMake.id == id)
   veh_make = veh_make_query.first()
   
   if veh_make == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Vehicle make with id: {id} does not exist")
  
         
   veh_make_query.delete(synchronize_session = False) 
   db.commit()  
   return Response(status_code=status.HTTP_204_NO_CONTENT)
############################################################################################################################

@router.put("/{id}", response_model=schemas.VehicleMakeCreate)
def update_veh_make(id:int,updated_veh_make:schemas.VehicleMakeCreate,db:Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
  
    veh_make_query = db.query(models.VehicleMake).filter(models.VehicleMake.id == id)
    veh_make =veh_make_query.first()
    if veh_make == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Vehicle Make with id: {id} does not exist")
   
    veh_make_query.update(updated_veh_make.dict(),synchronize_session = False)
    db.commit()
    return veh_make_query.first()  
############################################################################################################################