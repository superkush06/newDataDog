"""Environment-driven configuration for the X agent."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[4] / ".env")


@dataclass(frozen=True)
class XAgentConfig:
    target_handle: str
    keyword: str
    poll_interval_seconds: int
    dry_run: bool

    # X / Twitter
    x_bearer_token: str | None
    x_api_key: str | None
    x_api_secret: str | None
    x_access_token: str | None
    x_access_token_secret: str | None

    # Nimble
    nimble_api_key: str | None
    nimble_x_endpoint: str

    # Groq
    groq_api_key: str | None
    groq_model: str

    # Persistence
    db_path: Path

    @property
    def has_x_write_creds(self) -> bool:
        return all([
            self.x_api_key, self.x_api_secret,
            self.x_access_token, self.x_access_token_secret,
        ])

    @property
    def has_x_read_creds(self) -> bool:
        return bool(self.x_bearer_token) or self.has_x_write_creds

    @property
    def has_nimble(self) -> bool:
        return bool(self.nimble_api_key)


def load_config() -> XAgentConfig:
    repo_root = Path(__file__).resolve().parents[4]
    db_path = Path(os.environ.get("X_AGENT_DB_PATH") or repo_root / "backend" / "data" / "x_agent.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)

    return XAgentConfig(
        target_handle=os.environ.get("X_AGENT_TARGET_HANDLE", "arpitahujaa").lstrip("@"),
        keyword=os.environ.get("X_AGENT_KEYWORD", "crosby").lower(),
        poll_interval_seconds=int(os.environ.get("X_AGENT_POLL_INTERVAL", "60")),
        dry_run=os.environ.get("X_AGENT_DRY_RUN", "").lower() in {"1", "true", "yes"},
        x_bearer_token=os.environ.get("X_BEARER_TOKEN"),
        x_api_key=os.environ.get("X_API_KEY"),
        x_api_secret=os.environ.get("X_API_SECRET"),
        x_access_token=os.environ.get("X_ACCESS_TOKEN"),
        x_access_token_secret=os.environ.get("X_ACCESS_TOKEN_SECRET"),
        nimble_api_key=os.environ.get("NIMBLE_API_KEY"),
        nimble_x_endpoint=os.environ.get(
            "NIMBLE_X_ENDPOINT",
            "https://api.webit.live/api/v1/realtime/serp",
        ),
        groq_api_key=os.environ.get("GROQ_API_KEY"),
        groq_model=os.environ.get("X_AGENT_GROQ_MODEL", "llama-3.3-70b-versatile"),
        db_path=db_path,
    )
