from fastapi import FastAPI,Response, status, HTTPException, Depends, APIRouter
from typing import Optional,List, Dict 
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from .. import models ,schemas,oauth2,utils
from ..database import  get_db

router = APIRouter(prefix="/category_document", tags=['Category Document'])

############################################################################################################################
@router.post("/",status_code=status.HTTP_201_CREATED, response_model=schemas.CategoryDocumentOut) 
def create_cat_document(cat_document : schemas.CategoryDocumentCreate, db:Session = Depends(get_db)):
    
    
    new_cat_document = models.CategoryDocument(**cat_document.dict())
    db.add(new_cat_document)
    db.commit()
    db.refresh(new_cat_document)
    return new_cat_document

############################################################################################################################

@router.get("/", response_model = List[schemas.CategoryDocumentOut])
def get_documents(db:Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user),
              limit : int = 5, skip : int = 0, search :Optional[str] = ""):
              
  
    ##filter all documents at the same time
    documents = db.query(models.CategoryDocument).filter(models.CategoryDocument.doc_name.contains(search)).limit(limit).offset(skip).all()
    return documents
############################################################################################################################

@router.get("/{id}", response_model=schemas.CategoryDocumentOut)
def get_document(id : int, db :Session = Depends(get_db),  current_user : str = Depends(oauth2.get_current_user)):
    document = db.query(models.CategoryDocument).filter(models.CategoryDocument.id == id).first()
    
    if not document :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"document with id : {id} was not found")
    return document

#############################################################################################################################

@router.delete("/{id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_document(id:int,db:Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
   
   doc_query = db.query(models.CategoryDocument).filter(models.CategoryDocument.id == id)
   document = doc_query.first()
   
   if document == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"document with id: {id} does not exist")
       
   doc_query.delete(synchronize_session = False) 
   db.commit()  
   return Response(status_code=status.HTTP_204_NO_CONTENT)
############################################################################################################################

@router.put("/{id}", response_model=schemas.CategoryDocumentCreate)
def update_doc(id:int,updated_doc:schemas.CategoryDocumentCreate,db:Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
  
    doc_query = db.query(models.CategoryDocument).filter(models.CategoryDocument.id == id)
    document =doc_query.first()
    if document== None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"document with id: {id} does not exist")
   
    doc_query.update(updated_doc.dict(),synchronize_session = False)
    db.commit()
    return doc_query.first()  
############################################################################################################################