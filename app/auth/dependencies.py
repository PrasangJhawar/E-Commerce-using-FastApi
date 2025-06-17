from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.auth import models as auth_models
from app.auth.schemas import UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/signin")

#decodes jwt and extracts role
def get_current_user_role(token: str = Depends(oauth2_scheme)) -> UserRole:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        role_str: str = payload.get("role")
        if role_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials: role missing",
            )
        return UserRole(role_str) 
    except (JWTError, ValueError): 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

#admin check
def admin_required(role: UserRole = Depends(get_current_user_role)):
    if role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

#user check
def user_required(role: UserRole = Depends(get_current_user_role)):
    if role != UserRole.user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User privileges required",
        )

#fetches user using userID
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> auth_models.User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials: user ID missing",
            )
        user = db.query(auth_models.User).filter(auth_models.User.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

#returns id of the logged in user
def get_current_user_id(
    current_user: auth_models.User = Depends(get_current_user)
) -> str:
    return str(current_user.id)
