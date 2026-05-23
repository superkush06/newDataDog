from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gemini_api_key: str = ""
    nimble_api_key: str = ""
    luminai_api_key: str = ""

    clickhouse_host: str = ""
    clickhouse_port: int = 8443
    clickhouse_user: str = "default"
    clickhouse_password: str = ""

    database_url: str = ""
    redis_url: str = "redis://localhost:6379"

    dd_api_key: str = ""
    dd_service: str = "pulse"
    dd_env: str = "development"
    dd_agent_host: str = "localhost"

    x_bearer_token: str = ""
    x_webhook_secret: str = ""
    meta_app_secret: str = ""

    environment: str = "development"
    log_level: str = "INFO"
    cluster_similarity_threshold: float = 0.82
    merge_similarity_threshold: float = 0.88
    batch_size: int = 50


settings = Settings()

CHAR_LIMITS = {
    "x": 280,
    "instagram": 2200,
    "tiktok": 150,
    "reddit": 10000,
    "facebook": 8000,
}
