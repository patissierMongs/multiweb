"""Product models."""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean,
    DateTime, ForeignKey, Enum as SQLEnum, Index
)
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class ProductStatus(str, enum.Enum):
    """Product status."""
    AVAILABLE = "available"
    RESERVED = "reserved"
    SOLD = "sold"
    REMOVED = "removed"


class ProductCondition(str, enum.Enum):
    """Product condition."""
    NEW = "new"
    LIKE_NEW = "like_new"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class Category(Base):
    """Product category model."""

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    icon = Column(String(100))
    order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    parent = relationship("Category", remote_side=[id], backref="children")
    products = relationship("Product", back_populates="category")

    def __repr__(self):
        return f"<Category {self.name}>"


class Product(Base):
    """Product model."""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=False)
    price = Column(Float, nullable=False)
    original_price = Column(Float)

    # Details
    condition = Column(SQLEnum(ProductCondition), default=ProductCondition.GOOD)
    status = Column(SQLEnum(ProductStatus), default=ProductStatus.AVAILABLE, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Location
    location = Column(String(200))
    latitude = Column(Float)
    longitude = Column(Float)

    # Engagement
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    is_featured = Column(Boolean, default=False)
    is_negotiable = Column(Boolean, default=True)

    # SEO
    slug = Column(String(250), unique=True, index=True)
    meta_description = Column(String(300))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sold_at = Column(DateTime)
    deleted_at = Column(DateTime)

    # Relationships
    seller = relationship("User", back_populates="products")
    category = relationship("Category", back_populates="products")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="product")

    # Indexes for common queries
    __table_args__ = (
        Index('idx_product_status_created', 'status', 'created_at'),
        Index('idx_product_category_status', 'category_id', 'status'),
        Index('idx_product_seller_status', 'seller_id', 'status'),
    )

    def __repr__(self):
        return f"<Product {self.title}>"


class ProductImage(Base):
    """Product image model."""

    __tablename__ = "product_images"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500))
    order = Column(Integer, default=0)
    is_primary = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="images")

    def __repr__(self):
        return f"<ProductImage {self.id}>"
