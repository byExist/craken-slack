"""Slack settings loaded from environment variables.

Each concern is its own ``BaseSettings`` behind an ``@lru_cache`` getter (lazy
singleton, ``cache_clear()``-able in tests), grouped by vendor ``env_prefix``.
``Auth`` holds the one required secret — the Slack OAuth token — so a missing
token surfaces on the first API call, not at import, and the server can start
before it is set. ``Slack``/``Claude`` carry no required field, so reading e.g. a
cache path via ``get_slack()``/``get_claude()`` never needs the token.
"""

from functools import lru_cache
from typing import Any

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_TTL = 3600.0  # 1 hour


class Auth(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SLACK_")

    token: SecretStr


class Slack(BaseSettings):
    """Optional Slack-app runtime settings (no secret)."""

    model_config = SettingsConfigDict(env_prefix="SLACK_")

    cache_ttl: float = _DEFAULT_TTL

    @field_validator("cache_ttl", mode="before")
    @classmethod
    def _sane_ttl(cls, v: Any) -> float:
        """A bad ``SLACK_CACHE_TTL`` falls back to the default — a typo shouldn't
        break reads; negative also → default, and ``0`` disables expiry."""
        try:
            secs = float(v)
        except (TypeError, ValueError):
            return _DEFAULT_TTL
        return secs if secs >= 0 else _DEFAULT_TTL


class Claude(BaseSettings):
    """Values Claude Code injects into the plugin subprocess (``CLAUDE_*``)."""

    model_config = SettingsConfigDict(env_prefix="CLAUDE_")

    plugin_data: str | None = None  # CLAUDE_PLUGIN_DATA; absent outside a plugin


@lru_cache
def get_auth() -> Auth:
    return Auth()  # type: ignore


@lru_cache
def get_slack() -> Slack:
    return Slack()


@lru_cache
def get_claude() -> Claude:
    return Claude()
