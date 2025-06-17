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
import re
from jose import JWTError
from app.auth.schemas import Token
from jose import jwt


from app.core.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=schemas.UserResponse)
def signup(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        logger.debug("Signing up with email: %s", user_data.email)
        user = db.query(models.User).filter(models.User.email == user_data.email).first()
        if user:
            logger.warning("Signup failed: Email %s already registered", user_data.email)
            raise HTTPException(status_code=400, detail="Email is already registered")

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
        logger.info("User signed up successfully: %s", user.email)
        return user
    except Exception as e:
        logger.exception("Signup error: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
    

@router.post("/signin", response_model=schemas.Token)
#OAuth2 extracts data from x-www-form thing in postman
def signin(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    try:
        logger.debug("Signin attempt for email: %s", form_data.username)
        user = db.query(models.User).filter(models.User.email == form_data.username).first()
        if not user or not utils.verify_password(form_data.password, user.password):
            #credentials not matching
            logger.warning("Invalid signin attempt for email: %s", form_data.username)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        #token generation
        access_token = utils.create_access_token(data={"sub": str(user.id), "role": user.role})
        refresh_token = utils.create_refresh_token(data={"sub": str(user.id), "role": user.role})
        logger.info("User signed in successfully: %s", user.email)
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
    except Exception as e:
        logger.exception("Signin error: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/forgot-password", status_code=200)
def forgot_password(request: schemas.ForgotPasswordRequest, db: Session = Depends(get_db)):
    try:
        logger.debug("Forgot password request received for: %s", request.email)
        user = db.query(models.User).filter(models.User.email == request.email).first()
        if not user:
            logger.info("Password reset link sent (email not registered): %s", request.email)
            return {"msg": "if the email exists, a reset link has been sent"}

        reset_token = utils.create_password_reset_token(user.email)

        #sending reset email
        try:
            #smtp method, email.py
            send_reset_email(to_email=user.email, reset_token=reset_token)
            logger.info("Password reset email sent to: %s", user.email)
        except Exception as e:
            logger.exception("Failed to send reset email to %s: %s", user.email, str(e))
            raise HTTPException(status_code=500, detail="Failed to send reset email")

        return {"msg": "if the email exists, a reset link has been sent"}
    except Exception as e:
        logger.exception("Forgot password error: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

#generating a form for entering password
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
    #Form expects custom keys, for kvp we have OAuth2
    token: str = Form(...),
    new_password: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        logger.debug("Password reset attempt with token: %s", token)
        validate_strong_password(new_password)

        email = utils.verify_password_reset_token(token)
        if email is None:
            logger.warning("Invalid or expired password reset token used")
            raise HTTPException(status_code=400, detail="Invalid or expired token")

        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            logger.warning("Password reset failed: user not found for email: %s", email)
            raise HTTPException(status_code=400, detail="User not found")

        hashed_password = utils.hash_password(new_password)
        user.password = hashed_password
        db.commit()
        logger.info("Password reset successful for user: %s", email)
        return {"msg": "Password has been reset successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Reset password error: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")



#reset password strength checker
def validate_strong_password(password: str):
    if not re.search(r"[A-Z]", password):
        raise HTTPException(status_code=400, detail="must have uppercase")
    if not re.search(r"[a-z]", password):
        raise HTTPException(status_code=400, detail="must have lowercase")
    if not re.search(r"\d", password):
        raise HTTPException(status_code=400, detail="must have digit")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise HTTPException(status_code=400, detail="must have a special character")
    