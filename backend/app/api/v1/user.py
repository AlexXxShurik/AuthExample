import os

from fastapi import APIRouter, Depends, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.templating import Jinja2Templates

from backend.app.core.security import get_current_user
from backend.app.schemas.users import ResetPasswordRequest, UserUpdate, UserOut
from backend.app.services.user import UserService
from db.session import get_db

router = APIRouter(prefix="/users")
users = UserService()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@router.get("/me", response_model=UserOut)
async def get_me(current_user=Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserOut)
async def update_me(
    user_update: UserUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await users.update_user(db, current_user.id, user_update)


@router.delete("/me")
async def deactivate_me(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await users.deactivate_user(db, current_user.id)


@router.post("/password/forgot")
async def forgot_password(
    email: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    return await users.send_password_reset(db, request, email, background_tasks)


@router.get("/password/reset", response_class=HTMLResponse)
async def password_reset_page(request: Request, token: str):
    return templates.TemplateResponse("reset_password.html", {"request": request, "token": token})


@router.post("/password/reset")
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    return await users.reset_password(db, request.token, request.new_password)
