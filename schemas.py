from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List

class CategoryOut(BaseModel):
    id: int
    parent_id: Optional[int] = None
    name: str
    model_config = ConfigDict(from_attributes=True)

class CategoryTree(BaseModel):
    id: int
    name: str
    children: List["CategoryTree"] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)

class ProductOut(BaseModel):
    id: int
    name: str
    price: float
    stock: int
    category_id: int
    image: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)