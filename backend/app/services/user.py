import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, BackgroundTasks, Request
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.send_email import send_password_reset_email
from backend.app.models import User, PasswordResetToken
from backend.app.schemas.users import UserUpdate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    def __init__(self):
        self.pwd_context = pwd_context

    async def update_user(
        self, db: AsyncSession, user_id: int, user_update: UserUpdate
    ) -> User:
        user = await db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        for field, value in user_update.dict(exclude_unset=True).items():
            setattr(user, field, value)

        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def deactivate_user(self, db: AsyncSession, user_id: int) -> dict:
        user = await db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.is_active = False
        db.add(user)
        await db.commit()
        return {"detail": "User deactivated"}

    async def send_password_reset(
        self, db: AsyncSession, request: Request, email: str, background_tasks: BackgroundTasks
    ) -> dict:
        user_q = await db.execute(select(User).where(User.email == email))
        user = user_q.scalar_one_or_none()
        if not user:
            return {"detail": "If this email exists, a reset link will be sent"}

        token = secrets.token_urlsafe(32)
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
        )
        db.add(reset_token)
        await db.commit()

        send_password_reset_email(background_tasks, request, user.email, token)
        return {"detail": "Password reset email sent"}

    async def reset_password(
        self, db: AsyncSession, token: str, new_password: str
    ) -> dict:
        token_q = await db.execute(
            select(PasswordResetToken)
            .where(PasswordResetToken.token == token)
            .where(PasswordResetToken.expires_at > datetime.now(timezone.utc))
        )
        reset_token = token_q.scalar_one_or_none()
        if not reset_token:
            raise HTTPException(status_code=400, detail="Invalid or expired token")

        user = await db.get(User, reset_token.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.password_hash = self.pwd_context.hash(new_password)
        db.add(user)
        await db.delete(reset_token)
        await db.commit()
        return {"detail": "Password has been reset"}
