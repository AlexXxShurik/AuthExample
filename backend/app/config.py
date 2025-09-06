from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    API_VERSION: str = "1.0.0"
    DEBUG: bool = True
    CORS_ALLOWED_ORIGINS: list = [
        "http://actiadmin.ru",
        "http://www.actiadmin.ru",
        "http://api.actiadmin.ru",
        "http://www.api.actiadmin.ru",
        "https://actiadmin.ru",
        "https://actiadmin.ru/",
        "https://www.actiadmin.ru",
        "https://api.actiadmin.ru",
        "https://www.api.actiadmin.ru",
        "http://host",
        "http://host:3000",
        "http://host:8000",
        "http://host:6379",
        "http://host:443",
        "http://host:80",
        "http://localhost",
        "http://localhost:3000",
        "https://localhost:3000",
        "http://localhost:8000",
        "http://localhost:6379",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:6379",
        "http://localhost:63342",
        "http://localhost:50900",
        "http://127.0.0.1:50900",
    ]

    SMTP_SERVER: str
    SMTP_PORT: int
    SMTP_USERNAME: str
    SMTP_PASSWORD: str

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int

    SECRET_KEY: str
    ALGORITHM: str

    ACCESS_TOKEN_EXPIRE_MINUTES: int
    VERIFY_EMAIL_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    LIMIT_5_PER_MINUTE: str = "5/minute"
    LIMIT_10_PER_MINUTE: str = "10/minute"
    LIMIT_30_PER_MINUTE: str = "30/minute"
    LIMIT_60_PER_MINUTE: str = "60/minute"
    LIMIT_100_PER_MINUTE: str = "100/minute"
    LIMIT_1000_PER_DAY: str = "1000/day"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
