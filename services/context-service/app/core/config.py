from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = Field(default="context-service", alias="SERVICE_NAME")
    environment: str = Field(default="local", alias="ENVIRONMENT")

    database_url: str = Field(alias="DATABASE_URL")
    kafka_bootstrap_servers: str = Field(alias="KAFKA_BOOTSTRAP_SERVERS")
    encryption_key: str = Field(alias="ENCRYPTION_KEY")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


settings = Settings()