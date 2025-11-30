"""Product schemas."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class CategoryResponse(BaseModel):
    """Schema for category response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = None


class ProductImageResponse(BaseModel):
    """Schema for product image response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    thumbnail_url: Optional[str] = None
    order: int
    is_primary: bool


class ProductBase(BaseModel):
    """Base product schema."""
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10)
    price: float = Field(..., gt=0)
    original_price: Optional[float] = Field(None, gt=0)
    condition: str
    category_id: int
    location: Optional[str] = Field(None, max_length=200)
    is_negotiable: bool = True


class ProductCreate(ProductBase):
    """Schema for creating a product."""
    image_urls: Optional[List[str]] = []


class ProductUpdate(BaseModel):
    """Schema for updating a product."""
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    description: Optional[str] = Field(None, min_length=10)
    price: Optional[float] = Field(None, gt=0)
    original_price: Optional[float] = Field(None, gt=0)
    condition: Optional[str] = None
    status: Optional[str] = None
    location: Optional[str] = None
    is_negotiable: Optional[bool] = None


class ProductResponse(ProductBase):
    """Schema for product response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    status: str
    seller_id: int
    views: int
    likes: int
    is_featured: bool
    created_at: datetime
    updated_at: datetime
    images: List[ProductImageResponse] = []
    category: CategoryResponse


class ProductList(BaseModel):
    """Schema for product list response."""
    items: List[ProductResponse]
    total: int
    page: int
    page_size: int
    pages: int
