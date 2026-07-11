from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = Field(default="agent-service", alias="SERVICE_NAME")
    environment: str = Field(default="local", alias="ENVIRONMENT")

    database_url: str = Field(alias="DATABASE_URL")

    kafka_bootstrap_servers: str = Field(alias="KAFKA_BOOTSTRAP_SERVERS")
    context_events_topic: str = Field(alias="CONTEXT_EVENTS_TOPIC")
    agent_events_topic: str = Field(alias="AGENT_EVENTS_TOPIC")
    outbox_publish_interval_seconds: int = Field(default=5, alias="OUTBOX_PUBLISH_INTERVAL_SECONDS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


settings = Settings()