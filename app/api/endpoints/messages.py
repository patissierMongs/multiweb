"""Message endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.transaction import Message
from app.schemas.transaction import MessageCreate, MessageResponse

router = APIRouter()


@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    message_data: MessageCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Send a message to another user."""
    if message_data.receiver_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send message to yourself",
        )

    new_message = Message(
        sender_id=user_id,
        receiver_id=message_data.receiver_id,
        product_id=message_data.product_id,
        content=message_data.content,
        attachment_url=message_data.attachment_url,
    )

    db.add(new_message)
    await db.commit()
    await db.refresh(new_message)

    return new_message


@router.get("/", response_model=list[MessageResponse])
async def list_messages(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List all messages for current user."""
    query = select(Message).where(
        or_(
            Message.sender_id == user_id,
            Message.receiver_id == user_id,
        )
    ).order_by(Message.created_at.desc())

    result = await db.execute(query)
    messages = result.scalars().all()

    return messages
