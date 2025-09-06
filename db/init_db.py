import asyncio
from sqlalchemy import select

from db.session import engine, Base, AsyncSessionLocal
from backend.app.models.access import Role, BusinessObject, AccessRule


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        existing_roles = await db.execute(select(Role))
        if existing_roles.scalars().first():
            return

        roles = [
            Role(name="admin", description="Administrator with full access"),
            Role(name="manager", description="Manager with limited admin access"),
            Role(name="user", description="Regular user"),
            Role(name="guest", description="Guest user with minimal access"),
        ]

        for role in roles:
            db.add(role)

        await db.commit()

        objects = [
            BusinessObject(name="users", description="User management"),
            BusinessObject(name="products", description="Product catalog"),
            BusinessObject(name="orders", description="Customer orders"),
            BusinessObject(name="access_rules", description="Access control rules"),
        ]

        for obj in objects:
            db.add(obj)

        await db.commit()

        admin_role_result = await db.execute(select(Role).where(Role.name == "admin"))
        admin_role = admin_role_result.scalar_one()

        objects_result = await db.execute(select(BusinessObject))
        all_objects = objects_result.scalars().all()

        for obj in all_objects:
            access_rule = AccessRule(
                role_id=admin_role.id,
                object_id=obj.id,
                can_read=True,
                can_read_all=True,
                can_create=True,
                can_update=True,
                can_update_all=True,
                can_delete=True,
                can_delete_all=True,
            )
            db.add(access_rule)

        await db.commit()


async def main():
    await init_db()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
