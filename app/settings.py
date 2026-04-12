from pydantic import BaseSettings, Field


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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

