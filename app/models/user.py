"""User model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    """User roles."""
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    phone = Column(String(20))

    # Profile
    avatar_url = Column(String(500))
    bio = Column(String(500))
    location = Column(String(100))

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER)

    # Reputation
    rating = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)

    # Relationships
    products = relationship("Product", back_populates="seller", cascade="all, delete-orphan")
    transactions_as_buyer = relationship(
        "Transaction",
        foreign_keys="Transaction.buyer_id",
        back_populates="buyer"
    )
    transactions_as_seller = relationship(
        "Transaction",
        foreign_keys="Transaction.seller_id",
        back_populates="seller"
    )
    messages_sent = relationship(
        "Message",
        foreign_keys="Message.sender_id",
        back_populates="sender"
    )
    messages_received = relationship(
        "Message",
        foreign_keys="Message.receiver_id",
        back_populates="receiver"
    )
    reviews_given = relationship(
        "Review",
        foreign_keys="Review.reviewer_id",
        back_populates="reviewer"
    )
    reviews_received = relationship(
        "Review",
        foreign_keys="Review.reviewed_id",
        back_populates="reviewed"
    )

    def __repr__(self):
        return f"<User {self.username}>"
