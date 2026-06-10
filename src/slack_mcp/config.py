"""Slack settings loaded from environment variables.

A single secret — the Slack OAuth token. The workspace is implied by the token,
so no URL is needed. What the integration can *do* is governed by the token's
OAuth scopes (Slack enforces them server-side), not by app config — so there is
no read/write toggle here; see ``capabilities`` for how the tool surface tracks
the granted scopes.
"""

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Auth(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SLACK_")

    token: SecretStr


@lru_cache
def get_auth() -> Auth:
    return Auth()  # type: ignore
