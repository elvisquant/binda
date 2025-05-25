# app/routers/auth.py

from fastapi import APIRouter, Depends, status, HTTPException, Response
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import database, schemas, models, utils, oauth2 # Your project's modules

router = APIRouter(
    prefix="/login",  # All routes in this router will start with /login
    tags=['Authentication']
)

@router.post("/", response_model=schemas.Token) # Endpoint will be POST /login/
def login_for_access_token(
    user_credentials_form: OAuth2PasswordRequestForm = Depends(), # Expects form data
    db: Session = Depends(database.get_db)
):
    """
    Handles user login using username/email and password from form data.
    Returns an access token and user information upon successful authentication.
    """
    
    # The 'username' field from OAuth2PasswordRequestForm is used for the identifier
    identifier = user_credentials_form.username 
    password = user_credentials_form.password

    # Attempt to find the user by either email or username
    db_user = db.query(models.User).filter(
        (models.User.email == identifier) | (models.User.username == identifier)
    ).first()

    # Check if user exists and password is correct
    if not db_user or not utils.verify(password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"} 
        )

    # Check the user's account status (must be "active" to login)
    if db_user.status != "active":
        detail_message = f"Account access denied. Your account status is '{db_user.status}'."
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
    
    # Prepare data for the JWT payload (claims)
    # This should align with what schemas.TokenData expects and what oauth2.get_current_user will parse
    token_payload_data = {
        "sub": db_user.username,    # Standard subject claim (username)
        "user_id": db_user.id,      # Custom claim: integer user ID
        "status": db_user.status    # Custom claim: user's string status
        # Add other non-sensitive claims if needed, e.g., roles
    }
    
    access_token = oauth2.create_access_token(data=token_payload_data)
    
    # Return the response matching schemas.Token
    return schemas.Token(
        access_token=access_token,
        token_type="bearer",
        user_id=db_user.id,
        username=db_user.username,
        status=db_user.status
    )



    