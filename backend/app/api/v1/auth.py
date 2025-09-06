import os

from fastapi import APIRouter, Response, Depends, BackgroundTasks, Request
from fastapi.templating import Jinja2Templates
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.schemas.auth import UserOut, LoginRequest, UserCreate, TokenResponse
from backend.app.services.auth import AuthService
from db.session import get_db

router = APIRouter(prefix="/auth")
limiter = Limiter(key_func=get_remote_address)
auth_service = AuthService()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@router.post("/register", response_model=UserOut)
async def register(
    user_in: UserCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    return await auth_service.register_user(db, user_in, background_tasks, request)


@router.post("/login", response_model=TokenResponse)
async def login(
    login_in: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    return await auth_service.login_user(db, login_in, response)


@router.get("/verify-email")
async def verify_email(
    request: Request, token: str, db: AsyncSession = Depends(get_db)
):
    message, status_code = await auth_service.verify_email(db, token)
    template = "verify_success.html" if status_code == 200 else "verify_error.html"
    return templates.TemplateResponse(
        template, {"request": request, "message": message}, status_code=status_code
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    request: Request, response: Response, db: AsyncSession = Depends(get_db)
):
    return await auth_service.refresh_tokens(db, request, response)


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    return await auth_service.logout_user(db, request, response)
