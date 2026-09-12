from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_database: str = "cobeco"
    mysql_user: str = "cobeco"
    mysql_password: str
    jwt_secret: str = Field(min_length=32)
    app_env: str = "development"
    app_origin: str = "http://localhost:8000"
    recovery_mode: str = "question"
    seed_demo_password: str | None = None

    @model_validator(mode="after")
    def validate_environment(self):
        if self.recovery_mode not in {"question", "log"}:
            raise ValueError("RECOVERY_MODE deve ser question ou log")
        if self.app_env == "production" and self.recovery_mode == "log":
            raise ValueError("RECOVERY_MODE=log é exclusivo de desenvolvimento")
        if self.app_env == "production" and not self.app_origin.startswith("https://"):
            raise ValueError("APP_ORIGIN deve usar HTTPS em produção")
        return self
