"""Transaction endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.transaction import Transaction
from app.models.product import Product
from app.schemas.transaction import TransactionCreate, TransactionResponse

router = APIRouter()


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction_data: TransactionCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a new transaction."""
    # Get product
    result = await db.execute(
        select(Product).where(Product.id == transaction_data.product_id)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    if product.seller_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot buy your own product",
        )

    # Create transaction
    new_transaction = Transaction(
        product_id=transaction_data.product_id,
        buyer_id=user_id,
        seller_id=product.seller_id,
        amount=transaction_data.amount,
        payment_method=transaction_data.payment_method,
        meeting_location=transaction_data.meeting_location,
        meeting_time=transaction_data.meeting_time,
        buyer_notes=transaction_data.buyer_notes,
    )

    db.add(new_transaction)
    await db.commit()
    await db.refresh(new_transaction)

    return new_transaction


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get transaction by ID."""
    result = await db.execute(
        select(Transaction).where(Transaction.id == transaction_id)
    )
    transaction = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    if transaction.buyer_id != user_id and transaction.seller_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this transaction",
        )

    return transaction
