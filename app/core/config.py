from functools import lru_cache

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    admin_api_token: SecretStr
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("admin_api_token")
    @classmethod
    def check_token(cls, value: SecretStr) -> SecretStr:
        token = value.get_secret_value()
        if len(token) < 32 or token == "replace_with_long_random_admin_token":
            raise ValueError("ADMIN_API_TOKEN must be a non-default token of 32+ characters")
        return value

    @model_validator(mode="after")
    def check_database(self) -> "Settings":
        if not self.database_url.startswith("postgresql+asyncpg://"):
            raise ValueError("DATABASE_URL must use PostgreSQL asyncpg")
        if "replace_with_long_random_password" in self.database_url:
            raise ValueError("DATABASE_URL contains a placeholder password")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
