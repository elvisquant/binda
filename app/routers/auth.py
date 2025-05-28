# app/routers/auth.py

from fastapi import APIRouter, Depends, status, HTTPException, Response
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
# from datetime import timedelta # Not needed here anymore for this function

from .. import database, schemas, models, utils, oauth2 

router = APIRouter(
    prefix="/login", 
    tags=['Authentication']
)

@router.post("/", response_model=schemas.Token)
def login_for_access_token(
    user_credentials_form: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(database.get_db)
):
    identifier = user_credentials_form.username 
    password = user_credentials_form.password

    db_user = db.query(models.User).filter(
        (models.User.email == identifier) | (models.User.username == identifier)
    ).first()

    if not db_user or not utils.verify(password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"} 
        )

    if db_user.status != "active":
        detail_message = f"Account access denied. Your account status is '{db_user.status}'."
        # ... (your existing status detail messages) ...
        if db_user.status == "inactive":
            detail_message = "Your account is currently inactive. Please contact support to reactivate."
        elif db_user.status == "suspended":
            detail_message = "Your account has been suspended. Please contact support for assistance."
        elif db_user.status == "pending_approval":
            detail_message = "Your account is awaiting approval. Please check back later or contact support if you have questions."
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail_message
        )
    
    token_payload_data = {
        "sub": db_user.username,    
        "user_id": db_user.id,      
        "status": db_user.status    
    }
    
    # Call create_access_token WITHOUT expires_delta, as it's handled internally
    access_token = oauth2.create_access_token(data=token_payload_data) 
    
    return schemas.Token(
        access_token=access_token,
        token_type="bearer",
        user_id=db_user.id,
        username=db_user.username,
        status=db_user.status
    )



    