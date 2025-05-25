from fastapi import FastAPI,Response, status, HTTPException, Depends, APIRouter
from typing import Optional,List, Dict 
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from .. import models ,schemas,oauth2,utils
from ..database import  get_db

router = APIRouter(prefix="/category_panne", tags=['Category Panne'])
############################################################################################################################
@router.post("/",status_code=status.HTTP_201_CREATED, response_model=schemas.CategoryPanneOut) 
def create_category_panne(cat_panne : schemas.CategoryPanneCreate, db:Session = Depends(get_db)):
  
    new_Cat_panne= models.CategoryPanne(**cat_panne.dict())
    db.add(new_Cat_panne)
    db.commit()
    db.refresh(new_Cat_panne)
    return new_Cat_panne

############################################################################################################################

@router.get("/", response_model = List[schemas.CategoryPanneOut])
def get_panne_categories(db:Session = Depends(get_db),limit : int = 20, skip : int = 0, search :Optional[str] = ""):
              
  
    ##filter all panne categories at the same time
    pannes = db.query(models.CategoryPanne).filter(models.CategoryPanne.panne_name.contains(search)).limit(limit).offset(skip).all()
    return pannes
############################################################################################################################

@router.get("/{id}", response_model=schemas.CategoryPanneOut)
def get_panne_category(id : int, db :Session = Depends(get_db),  current_user : str = Depends(oauth2.get_current_user)):
    cat_panne = db.query(models.CategoryPanne).filter(models.CategoryPanne.id == id).first()
    
    if not cat_panne :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category Panne with id : {id} was not found")
    return cat_panne

#############################################################################################################################

@router.delete("/{id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_cat_panne(id:int,db:Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
   
   cat_panne_query = db.query(models.CategoryPanne).filter(models.CategoryPanne.id == id)
   cat_panne =cat_panne_query.first()
   
   if cat_panne == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Category Panne with id: {id} does not exist")
  
         
   cat_panne_query.delete(synchronize_session = False) 
   db.commit()  
   return Response(status_code=status.HTTP_204_NO_CONTENT)
############################################################################################################################

@router.put("/{id}", response_model=schemas.CategoryPanneCreate)
def update_cat_panne(id:int,updated_cat_panne:schemas.CategoryPanneCreate,db:Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
  
    cat_panne_query = db.query(models.User).filter(models.User.id == id)
    cat_panne =cat_panne_query.first()
    if cat_panne == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"user with id: {id} does not exist")
   
    cat_panne_query.update(updated_cat_panne.dict(),synchronize_session = False)
    db.commit()
    return cat_panne_query.first()  
############################################################################################################################