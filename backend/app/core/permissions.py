from fastapi import HTTPException, status, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.security import get_current_user
from backend.app.models.access import AccessRule, BusinessObject, UserRole
from backend.app.models.user import User
from db.session import get_db


async def check_permission(
    user: User, db: AsyncSession, object_name: str, action: str
) -> bool:
    if user.is_superuser:
        return True

    user_roles = await db.execute(select(UserRole).where(UserRole.user_id == user.id))
    user_roles = user_roles.scalars().all()
    role_ids = [ur.role_id for ur in user_roles]

    if not role_ids:
        return False

    business_object = await db.execute(
        select(BusinessObject).where(BusinessObject.name == object_name)
    )
    business_object = business_object.scalar_one_or_none()

    if not business_object:
        return False

    access_rules = await db.execute(
        select(AccessRule)
        .where(AccessRule.role_id.in_(role_ids))
        .where(AccessRule.object_id == business_object.id)
    )
    access_rules = access_rules.scalars().all()

    for rule in access_rules:
        if action == "read" and rule.can_read:
            return True
        elif action == "read_all" and rule.can_read_all:
            return True
        elif action == "create" and rule.can_create:
            return True
        elif action == "update" and rule.can_update:
            return True
        elif action == "update_all" and rule.can_update_all:
            return True
        elif action == "delete" and rule.can_delete:
            return True
        elif action == "delete_all" and rule.can_delete_all:
            return True

    return False


def require_permission(object_name: str, action: str):
    async def permission_dependency(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        has_permission = await check_permission(current_user, db, object_name, action)
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return current_user

    return permission_dependency
