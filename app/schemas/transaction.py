"""Transaction, Message, and Review schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# Transaction Schemas
class TransactionBase(BaseModel):
    """Base transaction schema."""
    product_id: int
    amount: float = Field(..., gt=0)
    payment_method: Optional[str] = None
    meeting_location: Optional[str] = None
    meeting_time: Optional[datetime] = None


class TransactionCreate(TransactionBase):
    """Schema for creating a transaction."""
    buyer_notes: Optional[str] = None


class TransactionUpdate(BaseModel):
    """Schema for updating a transaction."""
    status: Optional[str] = None
    meeting_location: Optional[str] = None
    meeting_time: Optional[datetime] = None
    seller_notes: Optional[str] = None
    cancellation_reason: Optional[str] = None


class TransactionResponse(TransactionBase):
    """Schema for transaction response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    buyer_id: int
    seller_id: int
    status: str
    buyer_notes: Optional[str] = None
    seller_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


# Message Schemas
class MessageCreate(BaseModel):
    """Schema for creating a message."""
    receiver_id: int
    product_id: Optional[int] = None
    content: str = Field(..., min_length=1, max_length=5000)
    attachment_url: Optional[str] = None


class MessageResponse(BaseModel):
    """Schema for message response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    sender_id: int
    receiver_id: int
    product_id: Optional[int] = None
    content: str
    is_read: bool
    attachment_url: Optional[str] = None
    created_at: datetime
    read_at: Optional[datetime] = None


# Review Schemas
class ReviewCreate(BaseModel):
    """Schema for creating a review."""
    transaction_id: int
    reviewed_id: int
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=1000)
    communication_rating: Optional[int] = Field(None, ge=1, le=5)
    punctuality_rating: Optional[int] = Field(None, ge=1, le=5)
    product_accuracy_rating: Optional[int] = Field(None, ge=1, le=5)


class ReviewResponse(BaseModel):
    """Schema for review response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_id: int
    reviewer_id: int
    reviewed_id: int
    rating: int
    comment: Optional[str] = None
    communication_rating: Optional[int] = None
    punctuality_rating: Optional[int] = None
    product_accuracy_rating: Optional[int] = None
    is_visible: bool
    created_at: datetime
