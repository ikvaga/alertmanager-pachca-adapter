from pydantic import BaseSettings


class Settings(BaseSettings):
    pachca_token: str
    pachca_base_url: str = "https://api.pachca.com/api/shared/v1"

    routes_path: str = "/config/routes.yaml"
    port: int = 8080

    message_max_alerts: int = 20

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

