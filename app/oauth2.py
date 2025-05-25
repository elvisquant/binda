# app/oauth2.py

from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from . import schemas, database, models
from .config import settings

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes # Will now be a clean int

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/") # Matches your auth.py

def create_access_token(data: dict):
    to_encode = data.copy()
    try:
        # Ensure ACCESS_TOKEN_EXPIRE_MINUTES is an integer
        expire_minutes = int(ACCESS_TOKEN_EXPIRE_MINUTES)
    except ValueError:
        print(f"ERROR: ACCESS_TOKEN_EXPIRE_MINUTES ('{ACCESS_TOKEN_EXPIRE_MINUTES}') is not a valid integer!")
        expire_minutes = 30 # Default to 30 minutes if config is bad

    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    to_encode.update({"exp": expire})

    print(f"\n--- STEP 4.1: Creating Token ---")
    print(f"Data for encoding (from auth.py): {data}")
    print(f"Full payload to encode (with exp): {to_encode}")
    print(f"Using SECRET_KEY (first 5 chars for log): {SECRET_KEY[:5]}...")
    print(f"Using ALGORITHM: {ALGORITHM}")
    print(f"Token Expiry Time (UTC): {expire}")

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    print(f"Generated encoded JWT: {encoded_jwt}")
    print(f"--- Token Created Successfully ---\n")
    return encoded_jwt


# In app/oauth2.py
def verify_access_token(token: str, credentials_exception: HTTPException) -> schemas.TokenData:
    print(f"\n--- STEP 5.1: Verifying Token ---")
    print(f"Received token for verification: {token}")
    print(f"Using SECRET_KEY (first 5 chars for log): {SECRET_KEY[:5]}...")
    print(f"Using ALGORITHM: {ALGORITHM}")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"STEP 5.2: Token decoded successfully. Payload: {payload}")
        
        subject: Optional[str] = payload.get("sub") 
        user_id_from_token: Optional[int] = payload.get("user_id")
        status_from_token: Optional[str] = payload.get("status")
        # username_from_token will be same as subject based on current create_access_token

        print(f"STEP 5.3: Extracted from payload - sub: {subject}, user_id: {user_id_from_token}, status: {status_from_token}")

        if subject is None or user_id_from_token is None or status_from_token is None:
            print(f"ERROR STEP 5.4: Missing critical claims after decoding. Cannot create TokenData.")
            raise credentials_exception
        
        # Ensure username is consistent with sub for TokenData
        token_data = schemas.TokenData(
            sub=subject,
            user_id=user_id_from_token,
            status=status_from_token,
            username=subject 
        )
        print(f"STEP 5.5: TokenData object created: {token_data.model_dump_json(indent=2)}")
    except JWTError as e:
        print(f"ERROR STEP 5.6: JWTError during token decoding: {str(e)}")
        # Common errors: "Signature verification failed", "Token has expired"
        raise credentials_exception
    except Exception as e:
        # This could be a Pydantic validation error if payload doesn't match TokenData
        print(f"ERROR STEP 5.7: Unexpected error during token verification (e.g., Pydantic validation): {str(e)}")
        raise credentials_exception
    
    print(f"--- Token Verified Successfully (verify_access_token) ---\n")
    return token_data

def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(database.get_db)
) -> models.User:
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = verify_access_token(token, credentials_exception)
    
    if token_data.user_id is None: # Should be caught earlier, but good safeguard
        print("Error in get_current_user: token_data.user_id is None after verification.")
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id == token_data.user_id).first()

    if user is None:
        print(f"Error in get_current_user: User with ID {token_data.user_id} not found in DB.")
        raise credentials_exception
    
    # Security Improvement: Re-check user status on every authenticated request
    if user.status != "active":
        print(f"Access denied for user ID {user.id}: Account status is '{user.status}'.")
        # You might want a more specific message or just the generic credentials_exception
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account access restricted. Status: {user.status}",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return user

