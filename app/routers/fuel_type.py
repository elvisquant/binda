from fastapi import FastAPI,Response, status, HTTPException, Depends, APIRouter
from typing import Optional,List, Dict 
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from .. import models ,schemas,oauth2,utils
from ..database import  get_db

router = APIRouter(prefix="/fuel_type", tags=['Fuel Type'])

############################################################################################################################
@router.post("/",status_code=status.HTTP_201_CREATED, response_model=schemas.FuelTypeOut) 
def create_fuel_type(typefuel : schemas.FuelTypeCreate, db:Session = Depends(get_db)):
    
    
    new_fueltype = models.FuelType(**typefuel.dict())
    db.add(new_fueltype)
    db.commit()
    db.refresh(new_fueltype)
    return new_fueltype

############################################################################################################################

@router.get("/", response_model = List[schemas.FuelTypeOut])
def get_type_fuel(db:Session = Depends(get_db),limit : int = 10, skip : int = 0, search :Optional[str] = ""):
              

    ##filter all type of fuel at the same time
    type_fuels = db.query(models.FuelType).filter(models.FuelType.fuel_type.contains(search)).limit(limit).offset(skip).all()
    return type_fuels 
############################################################################################################################

@router.get("/{id}", response_model=schemas.FuelTypeOut)
def get_typefuel(id : int, db :Session = Depends(get_db),  current_user : str = Depends(oauth2.get_current_user)):
    fuel_type = db.query(models.FuelType).filter(models.FuelType.id == id).first()
    
    if not fuel_type :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Fuel Type with id : {id} was not found")
    return fuel_type

#############################################################################################################################

@router.delete("/{id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_fuel_type(id:int,db:Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
   
   fueltype_query = db.query(models.FuelType).filter(models.FuelType.id == id)
   fueltype = fueltype_query.first()
   
   if fueltype == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Fuel Type with id: {id} does not exist")
  
         
   fueltype_query.delete(synchronize_session = False) 
   db.commit()  
   return Response(status_code=status.HTTP_204_NO_CONTENT)
############################################################################################################################

@router.put("/{id}", response_model=schemas.FuelTypeCreate)
def update_fueltype(id:int,updated_fueltype:schemas.FuelTypeCreate,db:Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
  
    fueltype_query = db.query(models.FuelType).filter(models.FuelType.id == id)
    fueltype =fueltype_query.first()
    if fueltype == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Fuel Type with id: {id} does not exist")
   
    fueltype_query.update(updated_fueltype.dict(),synchronize_session = False)
    db.commit()
    return fueltype_query.first()  
############################################################################################################################