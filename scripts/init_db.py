"""
Database initialization script.
Creates tables and populates initial data.
"""
import asyncio
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from sqlalchemy import select
from app.core.database import engine, AsyncSessionLocal, Base
from app.models import Category, User
from app.core.security import get_password_hash


async def create_tables():
    """Create all database tables."""
    print("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("✓ Tables created successfully")


async def create_initial_categories():
    """Create initial product categories."""
    print("Creating initial categories...")

    categories = [
        {"name": "전자제품", "slug": "electronics", "icon": "💻", "order": 1},
        {"name": "의류/패션", "slug": "fashion", "icon": "👔", "order": 2},
        {"name": "가구/인테리어", "slug": "furniture", "icon": "🛋️", "order": 3},
        {"name": "도서/티켓", "slug": "books-tickets", "icon": "📚", "order": 4},
        {"name": "스포츠/레저", "slug": "sports", "icon": "⚽", "order": 5},
        {"name": "유아/아동", "slug": "baby-kids", "icon": "🍼", "order": 6},
        {"name": "뷰티/미용", "slug": "beauty", "icon": "💄", "order": 7},
        {"name": "반려동물", "slug": "pets", "icon": "🐕", "order": 8},
        {"name": "식품", "slug": "food", "icon": "🍱", "order": 9},
        {"name": "기타", "slug": "others", "icon": "📦", "order": 10},
    ]

    async with AsyncSessionLocal() as session:
        # Check if categories already exist
        result = await session.execute(select(Category))
        existing = result.scalars().first()

        if not existing:
            for cat_data in categories:
                category = Category(**cat_data, is_active=True)
                session.add(category)

            await session.commit()
            print(f"✓ Created {len(categories)} categories")
        else:
            print("✓ Categories already exist")


async def create_demo_user():
    """Create a demo user for testing."""
    print("Creating demo user...")

    async with AsyncSessionLocal() as session:
        # Check if demo user exists
        result = await session.execute(
            select(User).where(User.email == "demo@multiweb.com")
        )
        existing = result.scalar_one_or_none()

        if not existing:
            demo_user = User(
                email="demo@multiweb.com",
                username="demo",
                hashed_password=get_password_hash("demo123!"),
                full_name="Demo User",
                location="Seoul, South Korea",
                bio="Demo account for testing",
                is_active=True,
                is_verified=True,
            )
            session.add(demo_user)
            await session.commit()
            print("✓ Demo user created (email: demo@multiweb.com, password: demo123!)")
        else:
            print("✓ Demo user already exists")


async def main():
    """Main initialization function."""
    print("="*60)
    print("MultiWeb Database Initialization")
    print("="*60)

    try:
        await create_tables()
        await create_initial_categories()
        await create_demo_user()

        print("="*60)
        print("✓ Database initialization completed successfully!")
        print("="*60)

    except Exception as e:
        print(f"✗ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
