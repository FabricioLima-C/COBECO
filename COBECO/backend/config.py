from typing import Literal
from urllib.parse import urlsplit

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
    app_env: Literal["development", "test", "production"] = "development"
    app_origin: str = "http://localhost:8000"
    recovery_mode: Literal["code", "question", "log"] = "code"
    seed_demo_password: str | None = None
    max_request_bytes: int = Field(default=65536, ge=16384, le=1048576)

    @model_validator(mode="after")
    def validate_environment(self):
        origin = urlsplit(self.app_origin)
        if (
            origin.scheme not in {"http", "https"}
            or not origin.hostname
            or origin.username
            or origin.password
            or origin.path
            or origin.query
            or origin.fragment
        ):
            raise ValueError("APP_ORIGIN deve conter apenas protocolo, host e porta, sem barra final")
        if "change-this" in self.jwt_secret.lower() or len(set(self.jwt_secret)) < 12:
            raise ValueError("JWT_SECRET deve ser uma chave aleatória própria, não um valor de exemplo")
        if self.app_env == "production":
            if self.recovery_mode != "code":
                raise ValueError("Produção exige RECOVERY_MODE=code")
            if origin.scheme != "https":
                raise ValueError("APP_ORIGIN deve usar HTTPS em produção")
            if self.seed_demo_password:
                raise ValueError("Conta demo não é permitida em produção")
            if not self.mysql_password or "change-this" in self.mysql_password.lower():
                raise ValueError("Configure uma senha MySQL própria em produção")
        return self
