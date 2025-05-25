from fastapi import FastAPI,Response, status, HTTPException, Depends, APIRouter
from typing import Optional,List, Dict 
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from .. import models ,schemas,oauth2,utils
from ..database import  get_db

router = APIRouter(prefix="/vehicle_model", tags=['Vehicle Model'])

############################################################################################################################
@router.post("/",status_code=status.HTTP_201_CREATED, response_model=schemas.VehicleModelOut) 
def create_veh_model(veh_model : schemas.VehicleModelCreate, db:Session = Depends(get_db)):
  
    new_veh_model = models.VehicleModel(**veh_model.dict())
    db.add(new_veh_model)
    db.commit()
    db.refresh(new_veh_model)
    return new_veh_model

############################################################################################################################

@router.get("/", response_model = List[schemas.VehicleModelOut])
def get_veh_models(db:Session = Depends(get_db),limit : int = 10, skip : int = 0, search :Optional[str] = ""):
              
  
    ##filter all vehicle Models at the same time
    veh_models = db.query(models.VehicleModel).filter(models.VehicleModel.vehicle_model.contains(search)).limit(limit).offset(skip).all()
    return veh_models
############################################################################################################################

@router.get("/{id}", response_model=schemas.VehicleModelOut)
def get_veh_model(id : int, db :Session = Depends(get_db),  current_user : str = Depends(oauth2.get_current_user)):
    veh_model = db.query(models.VehicleModel).filter(models.VehicleModel.id == id).first()
    
    if not veh_model :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Vehicle Model with id : {id} was not found")
    return veh_model

#############################################################################################################################

@router.delete("/{id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_veh_model(id:int,db:Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
   
   veh_model_query = db.query(models.VehicleModel).filter(models.VehicleModel.id == id)
   veh_model = veh_model_query.first()
   
   if veh_model == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Vehicle Model with id: {id} does not exist")
  
         
   veh_model_query.delete(synchronize_session = False) 
   db.commit()  
   return Response(status_code=status.HTTP_204_NO_CONTENT)
############################################################################################################################

@router.put("/{id}", response_model=schemas.VehicleModelCreate)
def update_veh_model(id:int,updated_veh_model:schemas.VehicleModelCreate,db:Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
  
    veh_model_query = db.query(models.VehicleModel).filter(models.VehicleModel.id == id)
    veh_model =veh_model_query.first()
    if veh_model == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Vehicle Model with id: {id} does not exist")
   
    veh_model_query.update(updated_veh_model.dict(),synchronize_session = False)
    db.commit()
    return veh_model_query.first()  
############################################################################################################################