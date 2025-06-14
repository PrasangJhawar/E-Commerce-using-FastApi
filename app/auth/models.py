import uuid
from sqlalchemy import Column, String, Boolean, DateTime, func, Enum
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from pydantic import field_validator
import re
import enum

class UserRole(str, enum.Enum):
    admin = "admin"
    user = "user"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.user, nullable=False)  #"admin" or "user" role only
    password = Column(String, nullable=False)  # storing hashed password here
