from pydantic import BaseModel, EmailStr, field_validator, constr, Field
from uuid import UUID
import re

class UserBase(BaseModel):
    name: str = Field(strip_whitespace=True, min_length=1)
    email: EmailStr
    role: str = Field(..., pattern="^(admin|user)$")

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

    #strong password checks
    @field_validator('password')
    def strong_password(cls, value):
        if not re.search(r"[A-Z]", value):
            raise ValueError("must have uppercase")
        if not re.search(r"[a-z]", value):
            raise ValueError("must have lowercase")
        if not re.search(r"\d", value):
            raise ValueError("must have digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise ValueError("must have special character")
        return value

class UserResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    role: str

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: str
    role: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

    @field_validator('new_password')
    def strong_password(cls, value):
        if not re.search(r"[A-Z]", value):
            raise ValueError("must have uppercase")
        if not re.search(r"[a-z]", value):
            raise ValueError("must have lowercase")
        if not re.search(r"\d", value):
            raise ValueError("must have digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise ValueError("must have special character")
        return value 