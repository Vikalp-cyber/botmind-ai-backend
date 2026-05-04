import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.db.models import Tenant, User, UserRole, TenantStatus
from app.core.security import hash_password
from app.core.config import get_settings

async def seed():
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Create Tenant
        tenant_id = uuid.UUID("a0acd427-1e52-46a1-bc3c-6096e0159866") # Use a fixed UUID for testing if possible
        tenant = Tenant(
            id=tenant_id,
            name="Dummy Corporation",
            slug="dummy",
            status=TenantStatus.ACTIVE
        )
        session.add(tenant)
        
        # Create User
        user = User(
            tenant=tenant,
            email="admin@dummy.com",
            password_hash=hash_password("password123"),
            full_name="Admin User",
            role=UserRole.ADMIN,
            is_active=True
        )
        session.add(user)
        
        await session.commit()
        print("Database seeded successfully!")
        print(f"Tenant ID: {tenant.id}")
        print(f"User Email: {user.email}")
        print("Password: password123")

if __name__ == "__main__":
    asyncio.run(seed())
