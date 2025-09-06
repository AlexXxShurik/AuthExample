import logging
import os
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import List

import colorlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.api.v1 import auth, user, example
from backend.app.config import settings
from db.init_db import init_db


def configure_logging(level=logging.INFO, log_file="logs/app.log") -> None:
    """Настройка цветного логирования с сохранением в файл и стандартными логами Uvicorn"""
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # === создаём папку, если её нет ===
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # === Консольный обработчик с цветами ===
    console_handler = colorlog.StreamHandler()
    console_handler.setFormatter(
        colorlog.ColoredFormatter(
            fmt="%(log_color)s%(levelname)s:     [%(asctime)s.%(msecs)03d] %(name)s %(message)s",
            datefmt="%d.%m.%Y - %H:%M:%S",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        )
    )

    # === Файловый обработчик с ротацией ===
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(
        logging.Formatter(
            fmt="%(levelname)s:     [%(asctime)s.%(msecs)03d] %(name)s %(message)s",
            datefmt="%d.%m.%Y - %H:%M:%S",
        )
    )

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.setLevel(level)


logger = logging.getLogger(__name__)
configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Контекст жизненного цикла приложения"""
    logger.info("Starting Acti API application")
    await init_db()
    yield
    logger.info("Shutting down Acti API application")


def configure_cors(app: FastAPI, allowed_origins: List[str]) -> None:
    """Настройка CORS middleware"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = app.openapi()
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    }
    openapi_schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def configure_static_files(app: FastAPI) -> None:
    """Настройка статических файлов"""
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True, parents=True)
    app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


def configure_routers(app: FastAPI) -> None:
    """Регистрация всех роутеров"""
    html_routers = []

    api_routers = [
        (auth.router, "auth"),
        (user.router, "user"),
        (example.router, "example"),
    ]

    superusers_routers = []

    websocket_routers = []

    for router, tag in html_routers:
        app.include_router(router, prefix="", tags=[tag])

    for router, tag in api_routers:
        app.include_router(router, prefix="/v1", tags=[tag])

    for router, tag in superusers_routers:
        app.include_router(router, prefix="/v1/superusers", tags=[tag])

    for router, tag in websocket_routers:
        app.include_router(router, prefix="/v1", tags=[tag])


def create_app() -> FastAPI:
    """Фабрика для создания экземпляра FastAPI"""
    app = FastAPI(
        title="UP AI API",
        version=settings.API_VERSION,
        description="""
        API for UP bot
        """,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan,
        debug=settings.DEBUG,
        openapi=custom_openapi,
    )

    configure_cors(app, settings.CORS_ALLOWED_ORIGINS)
    configure_routers(app)
    configure_static_files(app)

    return app


app = create_app()
