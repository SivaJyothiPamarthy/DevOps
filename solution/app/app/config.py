"""12-factor configuration: everything comes from environment variables."""

import os
from dataclasses import dataclass, field


def _env(name: str, default: str):
    return field(default_factory=lambda: os.getenv(name, default))


@dataclass(frozen=True)
class Config:
    app_env: str = _env("APP_ENV", "local")
    log_level: str = _env("LOG_LEVEL", "INFO")
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8080")))
    max_amount_sek: float = field(
        default_factory=lambda: float(os.getenv("MAX_AMOUNT_SEK", "100000"))
    )
    version: str = _env("APP_VERSION", "dev")
