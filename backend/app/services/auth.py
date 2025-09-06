import secrets
from datetime import datetime, timedelta, timezone

from fastapi import BackgroundTasks, HTTPException, status, Response, Request
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    get_user_id_and_jti_from_token,
)
from backend.app.core.send_email import send_verification_email
from backend.app.models import User, VerificationToken, UserSession, Role, UserRole
from backend.app.schemas.auth import UserCreate, LoginRequest, TokenResponse

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)

    async def register_user(
        self,
        db: AsyncSession,
        user_data: UserCreate,
        background_tasks: BackgroundTasks,
        request,
    ) -> User:
        user = await self._create_user(db, user_data)
        await self._assign_default_role(db, user)
        await self._create_verification_token(db, user)
        send_verification_email(
            background_tasks, request, user.email, user.verification_token.token
        )
        return user

    async def _create_user(self, db: AsyncSession, user_data: UserCreate) -> User:
        existing = await db.execute(select(User).where(User.email == user_data.email))
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists"
            )

        hashed_password = self.get_password_hash(user_data.password)
        user = User(
            email=user_data.email,
            password_hash=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            patronymic=user_data.patronymic,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def _create_verification_token(self, db: AsyncSession, user: User):
        token = secrets.token_urlsafe(32)
        verification_token = VerificationToken(
            user_id=user.id,
            token=token,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
        db.add(verification_token)
        await db.commit()
        user.verification_token = verification_token

    async def verify_email(self, db: AsyncSession, token: str) -> tuple[str, int]:
        verification_token = await db.execute(
            select(VerificationToken).where(
                VerificationToken.token == token,
                VerificationToken.expires_at > datetime.now(timezone.utc),
            )
        )
        token_obj = verification_token.scalar_one_or_none()
        if not token_obj:
            return "Invalid or expired verification token", status.HTTP_400_BAD_REQUEST

        user = await db.get(User, token_obj.user_id)
        if not user:
            return "User not found", status.HTTP_404_NOT_FOUND

        user.is_verified = True
        user.is_active = True
        await db.delete(token_obj)
        await db.commit()
        return "Email verified successfully", status.HTTP_200_OK

    async def login_user(
        self, db: AsyncSession, login_data: LoginRequest, response: Response
    ) -> TokenResponse:
        user = await self._get_user_by_credentials(db, login_data)
        return await self._create_tokens_for_user(db, user, response)

    async def _get_user_by_credentials(
        self, db: AsyncSession, login_data: LoginRequest
    ) -> User:
        user_q = await db.execute(select(User).where(User.email == login_data.email))
        user = user_q.scalar_one_or_none()
        if not user or not self.verify_password(
            login_data.password, user.password_hash
        ):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if not user.is_active:
            raise HTTPException(status_code=401, detail="Account is not active")
        if not user.is_verified:
            raise HTTPException(status_code=401, detail="Email not verified")
        return user

    async def _create_tokens_for_user(
        self, db: AsyncSession, user: User, response: Response
    ) -> TokenResponse:
        access_jti = secrets.token_urlsafe(16)
        refresh_jti = secrets.token_urlsafe(16)

        access_token = create_access_token(user.id, access_jti)
        refresh_token = create_refresh_token(user.id, refresh_jti)

        await self._create_sessions(db, user.id, access_jti, refresh_jti)
        self._set_refresh_cookie(response, refresh_token)

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    async def _create_sessions(
        self, db: AsyncSession, user_id: int, access_jti: str, refresh_jti: str
    ):
        access_session = UserSession(
            user_id=user_id,
            jti=access_jti,
            expires_at=datetime.now(timezone.utc)
            + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        refresh_session = UserSession(
            user_id=user_id,
            jti=refresh_jti,
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        db.add_all([access_session, refresh_session])
        await db.commit()

    def _set_refresh_cookie(self, response: Response, refresh_token: str):
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )

    async def logout_user(
        self, db: AsyncSession, request: Request, response: Response
    ) -> dict:
        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            raise HTTPException(status_code=401, detail="No refresh token provided")

        user_id, refresh_jti = get_user_id_and_jti_from_token(
            refresh_token, token_type="refresh"
        )
        await self._delete_user_sessions(db, user_id, refresh_jti)
        response.delete_cookie("refresh_token")
        return {"detail": "Successfully logged out"}

    async def refresh_tokens(
        self, db: AsyncSession, request: Request, response: Response
    ) -> TokenResponse:
        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            raise HTTPException(status_code=401, detail="No refresh token provided")

        user_id, refresh_jti = get_user_id_and_jti_from_token(
            refresh_token, token_type="refresh"
        )
        await self._delete_user_sessions(db, user_id, refresh_jti)

        new_access_jti = secrets.token_urlsafe(16)
        new_refresh_jti = secrets.token_urlsafe(16)

        new_access_token = create_access_token(user_id, new_access_jti)
        new_refresh_token = create_refresh_token(user_id, new_refresh_jti)
        await self._create_sessions(db, user_id, new_access_jti, new_refresh_jti)
        self._set_refresh_cookie(response, new_refresh_token)

        return TokenResponse(
            access_token=new_access_token, refresh_token=new_refresh_token
        )

    async def _delete_user_sessions(
        self, db: AsyncSession, user_id: int, refresh_jti: str
    ):
        session_q = await db.execute(
            select(UserSession).where(UserSession.jti == refresh_jti)
        )
        refresh_session = session_q.scalar_one_or_none()
        if refresh_session:
            await db.delete(refresh_session)

        access_q = await db.execute(
            select(UserSession).where(UserSession.user_id == user_id)
        )
        for session in access_q.scalars().all():
            await db.delete(session)
        await db.commit()

    async def _assign_default_role(self, db: AsyncSession, user: User):
        """Присвоение роли 'user' новому пользователю"""
        result = await db.execute(select(Role).where(Role.name == "user"))
        role_user = result.scalar_one_or_none()
        if not role_user:
            raise HTTPException(
                status_code=500, detail="Default role 'user' not found in DB"
            )

        user_role = UserRole(user_id=user.id, role_id=role_user.id)
        db.add(user_role)
        await db.commit()
