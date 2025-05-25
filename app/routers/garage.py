from fastapi import FastAPI,Response, status, HTTPException, Depends, APIRouter
from typing import Optional,List, Dict 
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from .. import models ,schemas,oauth2,utils
from ..database import  get_db

router = APIRouter(prefix="/garage", tags=['Garage'])
############################################################################################################################
@router.post("/",status_code=status.HTTP_201_CREATED, response_model=schemas.GarageCreate) 
def create_garage(garage : schemas.GarageCreate, db:Session = Depends(get_db)):
    

    new_garage = models.Garage(**garage.dict())
    db.add(new_garage)
    db.commit()
    db.refresh(new_garage)
    return new_garage

############################################################################################################################

@router.get("/", response_model = List[schemas.GarageOut])
def get_garage(db:Session = Depends(get_db),limit : int = 20, skip : int = 0, search :Optional[str] = ""):
              
  
    ##filter all garages at the same time
    garages = db.query(models.Garage).filter(models.Garage.nom_garage.contains(search)).limit(limit).offset(skip).all()
    return garages
############################################################################################################################

@router.get("/{id}", response_model=schemas.GarageOut)
def get_garage(id : int, db :Session = Depends(get_db),  current_user : str = Depends(oauth2.get_current_user)):
    garage = db.query(models.Garage).filter(models.Garage.id == id).first()
    
    if not garage :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Garage with id : {id} was not found")
    return garage

#############################################################################################################################

@router.delete("/{id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_garage(id:int,db:Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
   
   garage_query = db.query(models.Garage).filter(models.Garage.id == id)
   garage = garage_query.first()
   
   if garage == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Garage with id: {id} does not exist")
  
         
   garage_query.delete(synchronize_session = False) 
   db.commit()  
   return Response(status_code=status.HTTP_204_NO_CONTENT)
############################################################################################################################

@router.put("/{id}", response_model=schemas.GarageCreate)
def update_garage(id:int,updated_garage:schemas.GarageCreate,db:Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
  
    garage_query = db.query(models.User).filter(models.User.id == id)
    garage =garage_query.first()
    if garage == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"user with id: {id} does not exist")
   
    garage_query.update(updated_garage.dict(),synchronize_session = False)
    db.commit()
    return garage_query.first()  
############################################################################################################################