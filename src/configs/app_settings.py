from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    tuya_client_id: str
    tuya_secret: str
    tuya_project_code: str

    telegram_token: str
    telegram_proxy_string: Optional[str] = None

    verbose: bool = False


def get_settings() -> AppSettings:
    return AppSettings()  # type: ignore
