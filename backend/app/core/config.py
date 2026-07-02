from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "JotPop API"
    app_version: str = "0.33.0"

    database_url: str

    backend_port: int = 8000
    frontend_port: int = 5173
    frontend_allowed_origins: str = ""

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7

    # Comma-separated list. For the local MVP, ale@example.com is the dev account.
    # Normal users never see or access dev/debug tools.
    dev_user_emails: str = "ale@example.com"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def normalized_database_url(self) -> str:
        """Return a SQLAlchemy-compatible database URL.

        Some managed platforms expose Postgres URLs with the older postgres://
        scheme. SQLAlchemy expects postgresql:// or an explicit driver scheme.
        """
        if self.database_url.startswith("postgres://"):
            return self.database_url.replace("postgres://", "postgresql://", 1)
        return self.database_url

    @property
    def frontend_origin_list(self) -> list[str]:
        configured = [
            origin.strip().rstrip("/")
            for origin in self.frontend_allowed_origins.split(",")
            if origin.strip()
        ]
        defaults = [
            f"http://localhost:{self.frontend_port}",
            f"http://127.0.0.1:{self.frontend_port}",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
        # Keep order, avoid duplicates.
        seen = set()
        origins: list[str] = []
        for origin in configured + defaults:
            if origin not in seen:
                origins.append(origin)
                seen.add(origin)
        return origins

    @property
    def dev_email_set(self) -> set[str]:
        return {
            email.strip().lower()
            for email in self.dev_user_emails.split(",")
            if email.strip()
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Production note:
# FRONTEND_ALLOWED_ORIGINS must be set in production as a comma-separated list, e.g.
# https://your-jotpop-frontend.vercel.app,https://www.your-domain.com
