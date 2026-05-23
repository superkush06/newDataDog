import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Single global .env lives at the repo root.
# backend/app/config.py → up 3 dirs → repo root.
ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"

# macOS Python ships without trusted CA roots in the default ssl context, so
# aiohttp/redis-py fail TLS verification against Supabase, ClickHouse Cloud,
# Upstash, etc. Point both SSL_CERT_FILE and REQUESTS_CA_BUNDLE at certifi's
# bundle before any client library creates an SSL context.
if not os.environ.get("SSL_CERT_FILE"):
    try:
        import certifi
        os.environ["SSL_CERT_FILE"] = certifi.where()
        os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
    except ImportError:
        pass


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ROOT_ENV), extra="ignore")

    groq_api_key: str = ""
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
