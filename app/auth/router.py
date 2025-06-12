from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from app.core.database import get_db
from app.auth import models, schemas, utils
from app.core.config import settings
from datetime import timedelta
from app.utils.email import send_reset_email
from fastapi.responses import HTMLResponse
from fastapi import Form


router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=schemas.UserResponse)
def signup(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = utils.hash_password(user_data.password)
    user = models.User(
        name=user_data.name,
        email=user_data.email,
        role=user_data.role,
        password=hashed_password,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/signin", response_model=schemas.Token)
def signin(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not utils.verify_password(form_data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = utils.create_access_token(data={"sub": str(user.id), "role": user.role})
    refresh_token = utils.create_refresh_token(data={"sub": str(user.id), "role": user.role})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/forgot-password", status_code=200)
def forgot_password(request: schemas.ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if not user:
        return {"msg": "reset link has been sent on your email"}

    reset_token = utils.create_password_reset_token(user.email)

    #sending reset email
    try:
        send_reset_email(to_email=user.email, reset_token=reset_token)
    except Exception as e:
        print(f"Failed to send reset email: {e}")
        raise HTTPException(status_code=500, detail="Failed to send reset email")

    return {"msg": "if the email exists, a reset link has been sent"}


@router.get("/reset-password", response_class=HTMLResponse)
async def reset_password_form(token: str):
    html_content = f"""
    <html>
        <body>
            <form action="/auth/reset-password" method="post">
                <input type="hidden" name="token" value="{token}" />
                <label>New Password:</label>
                <input type="password" name="new_password" />
                <button type="submit">Reset Password</button>
            </form>
        </body>
    </html>
    """
    return html_content


@router.post("/reset-password", status_code=200)
def reset_password(
    token: str = Form(...),
    new_password: str = Form(...),
    db: Session = Depends(get_db)
):
    email = utils.verify_password_reset_token(token)
    
    #no email found
    if email is None:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    #setting new password
    hashed_password = utils.hash_password(new_password)
    user.password = hashed_password
    db.commit()
    return {"msg": "Password has been reset successfully"}