"""Transaction, Message, and Review models."""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean,
    DateTime, ForeignKey, Enum as SQLEnum, CheckConstraint
)
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class TransactionStatus(str, enum.Enum):
    """Transaction status."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


class PaymentMethod(str, enum.Enum):
    """Payment method."""
    CASH = "cash"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    MOBILE_PAYMENT = "mobile_payment"


class Transaction(Base):
    """Transaction model."""

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Transaction details
    amount = Column(Float, nullable=False)
    payment_method = Column(SQLEnum(PaymentMethod))
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.PENDING, index=True)

    # Meeting details
    meeting_location = Column(String(300))
    meeting_time = Column(DateTime)

    # Notes
    buyer_notes = Column(Text)
    seller_notes = Column(Text)
    cancellation_reason = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    cancelled_at = Column(DateTime)

    # Relationships
    product = relationship("Product", back_populates="transactions")
    buyer = relationship("User", foreign_keys=[buyer_id], back_populates="transactions_as_buyer")
    seller = relationship("User", foreign_keys=[seller_id], back_populates="transactions_as_seller")

    # Constraints
    __table_args__ = (
        CheckConstraint('buyer_id != seller_id', name='buyer_seller_different'),
        CheckConstraint('amount > 0', name='amount_positive'),
    )

    def __repr__(self):
        return f"<Transaction {self.id}>"


class Message(Base):
    """Message model for chat between users."""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), index=True)

    # Message content
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)

    # Attachments
    attachment_url = Column(String(500))
    attachment_type = Column(String(50))  # image, file, etc.

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    read_at = Column(DateTime)
    deleted_at = Column(DateTime)

    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], back_populates="messages_sent")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="messages_received")

    # Constraints
    __table_args__ = (
        CheckConstraint('sender_id != receiver_id', name='sender_receiver_different'),
    )

    def __repr__(self):
        return f"<Message {self.id}>"


class Review(Base):
    """Review model for user ratings."""

    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), unique=True, index=True)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    reviewed_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Review content
    rating = Column(Integer, nullable=False)  # 1-5 stars
    comment = Column(Text)

    # Review aspects (optional detailed ratings)
    communication_rating = Column(Integer)
    punctuality_rating = Column(Integer)
    product_accuracy_rating = Column(Integer)

    # Moderation
    is_visible = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    reviewer = relationship("User", foreign_keys=[reviewer_id], back_populates="reviews_given")
    reviewed = relationship("User", foreign_keys=[reviewed_id], back_populates="reviews_received")

    # Constraints
    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='rating_range'),
        CheckConstraint('reviewer_id != reviewed_id', name='reviewer_reviewed_different'),
    )

    def __repr__(self):
        return f"<Review {self.id}>"
