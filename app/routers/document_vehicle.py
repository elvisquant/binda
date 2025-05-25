from fastapi import FastAPI,Response, status, HTTPException, Depends, APIRouter
from typing import Optional,List, Dict 
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from .. import models ,schemas,oauth2,utils
from ..database import  get_db

router = APIRouter(prefix="/document_vehicle", tags=['Document vehicle'])

############################################################################################################################
@router.post("/",status_code=status.HTTP_201_CREATED, response_model=schemas.DocumentVehiculeOut) 
def create_doc_vehicle(doc_vehicle : schemas.DocumentVehiculeCreate, db:Session = Depends(get_db)):
 
    new_doc_vehicle = models.DocumentVehicule(**doc_vehicle.dict())
    db.add(new_doc_vehicle)
    db.commit()
    db.refresh(new_doc_vehicle)
    return new_doc_vehicle

############################################################################################################################

@router.get("/", response_model = List[schemas.DocumentVehiculeOut])
def get_vehicle_documents(db:Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user),
              limit : int = 5, skip : int = 0, search :Optional[str] = ""):
              
  
    ##filter all  vehicle documents at the same time
    vehicle_docs = db.query(models.DocumentVehicule).filter(models.DocumentVehicule.doc_name_id.contains(search)).limit(limit).offset(skip).all()
    return vehicle_docs 
############################################################################################################################

@router.get("/{id}", response_model=schemas.DocumentVehiculeOut)
def get_vehicle_doc(id : int, db :Session = Depends(get_db),  current_user : str = Depends(oauth2.get_current_user)):
    veh_doc = db.query(models.DocumentVehicule).filter(models.DocumentVehicule.id == id).first()
    
    if not veh_doc :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Vehicle document with id : {id} was not found")
    return veh_doc

#############################################################################################################################

@router.delete("/{id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_veh_doc(id:int,db:Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
   
   vehicle_doc_query = db.query(models.DocumentVehicule).filter(models.DocumentVehicule.id == id)
   vehicle_doc = vehicle_doc_query.first()
   
   if vehicle_doc == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Vehicle document with id: {id} does not exist")
  
         
   vehicle_doc_query.delete(synchronize_session = False) 
   db.commit()  
   return Response(status_code=status.HTTP_204_NO_CONTENT)
############################################################################################################################

@router.put("/{id}", response_model=schemas.DocumentVehiculeCreate)
def update_user(id:int,updated_veh_doc:schemas.DocumentVehiculeCreate,db:Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
  
    vehicle_doc_query = db.query(models.DocumentVehicule).filter(models.DocumentVehicule.id == id)
    vehicle_doc =vehicle_doc_query.first()
    if vehicle_doc == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Vehicle document with id: {id} does not exist")
   
    vehicle_doc_query.update(updated_veh_doc.dict(),synchronize_session = False)
    db.commit()
    return vehicle_doc_query.first()  
############################################################################################################################