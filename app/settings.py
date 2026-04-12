from typing import Optional

from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    pachca_token: str = Field(..., env="PACHCA_TOKEN")
    pachca_base_url: str = Field(
        "https://api.pachca.com/api/shared/v1",
        env="PACHCA_BASE_URL",
    )

    routes_path: str = Field("/config/routes.yaml", env="ROUTES_PATH")
    port: int = Field(8080, env="PORT")

    message_max_alerts: int = Field(20, env="MESSAGE_MAX_ALERTS")

    webhook_token: str | None = Field(None, env="WEBHOOK_TOKEN")

    pachca_timeout_seconds: float = Field(15.0, env="PACHCA_TIMEOUT_SECONDS")
    pachca_max_attempts: int = Field(3, env="PACHCA_MAX_ATTEMPTS")

    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_format: str = Field("text", env="LOG_FORMAT")
    log_file_path: Optional[str] = Field(None, env="LOG_FILE_PATH")
    log_file_max_megabytes: int = Field(10, env="LOG_FILE_MAX_MB")
    log_file_backup_count: int = Field(5, env="LOG_FILE_BACKUP_COUNT")

    @validator("log_format")
    @classmethod
    def normalize_log_format(cls, v: str) -> str:
        x = (v or "text").lower()
        if x not in ("text", "json"):
            raise ValueError("LOG_FORMAT must be text or json")
        return x

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

