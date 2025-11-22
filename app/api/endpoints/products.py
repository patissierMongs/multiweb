"""Product endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.product import Product, ProductImage, ProductStatus
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse, ProductList

router = APIRouter()


@router.get("/", response_model=ProductList)
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List products with pagination and filters."""
    query = select(Product).options(
        selectinload(Product.images),
        selectinload(Product.category)
    )

    # Apply filters
    if status:
        query = query.where(Product.status == status)
    else:
        query = query.where(Product.status == ProductStatus.AVAILABLE)

    if category_id:
        query = query.where(Product.category_id == category_id)

    if search:
        query = query.where(
            Product.title.ilike(f"%{search}%") | Product.description.ilike(f"%{search}%")
        )

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    query = query.order_by(Product.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    products = result.scalars().all()

    return ProductList(
        items=products,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get product by ID."""
    query = select(Product).options(
        selectinload(Product.images),
        selectinload(Product.category)
    ).where(Product.id == product_id)

    result = await db.execute(query)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    # Increment views
    product.views += 1
    await db.commit()

    return product


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a new product."""
    # Create slug from title
    slug = product_data.title.lower().replace(" ", "-")[:250]

    new_product = Product(
        title=product_data.title,
        description=product_data.description,
        price=product_data.price,
        original_price=product_data.original_price,
        condition=product_data.condition,
        category_id=product_data.category_id,
        location=product_data.location,
        is_negotiable=product_data.is_negotiable,
        seller_id=user_id,
        slug=slug,
    )

    db.add(new_product)
    await db.flush()

    # Add images
    if product_data.image_urls:
        for idx, url in enumerate(product_data.image_urls):
            image = ProductImage(
                product_id=new_product.id,
                url=url,
                order=idx,
                is_primary=(idx == 0),
            )
            db.add(image)

    await db.commit()
    await db.refresh(new_product)

    return new_product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update a product."""
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    if product.seller_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this product",
        )

    # Update fields
    for field, value in product_data.model_dump(exclude_unset=True).items():
        setattr(product, field, value)

    await db.commit()
    await db.refresh(product)

    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a product (soft delete)."""
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    if product.seller_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this product",
        )

    product.status = ProductStatus.REMOVED
    await db.commit()
