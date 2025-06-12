from pydantic import BaseModel, HttpUrl
from pydantic import BaseModel, HttpUrl

from uuid import UUID
from typing import Optional
from pydantic import BaseModel, HttpUrl 
from typing import Optional

from pydantic import BaseModel, field_validator, Field
from typing import Optional

class ProductBase(BaseModel):
    name: str = Field(strip_whitespace=True, min_length=1)
    description: Optional[str]
    price: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)
    category: Optional[str]
    image_url: Optional[str]


class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: UUID

    class Config:
        orm_mode = True
