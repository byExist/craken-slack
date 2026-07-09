"""Base model for Slack schemas."""

from collections.abc import Iterable
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    SerializerFunctionWrapHandler,
    model_serializer,
)


def keep_present(items: Iterable[tuple[str, Any]]) -> dict[str, Any]:
    """Keep every present value — empty ones included (``""``, ``{}``, ``[]``,
    ``0``, ``False``) — dropping only ``None`` (absence): "present but empty" is
    distinct from absent."""
    return {k: v for k, v in items if v is not None}


class SlackModel(BaseModel):
    """Base model for Slack JSON.

    Slack already returns snake_case keys, so no alias generation is needed
    (unlike Atlassian's camelCase). Unknown fields are ignored (Slack sends
    many). Serialization drops only ``None`` (see ``_drop_none``) to stay
    compact while preserving empty values.
    """

    model_config = ConfigDict(populate_by_name=True)

    @model_serializer(mode="wrap")
    def _drop_none(self, handler: SerializerFunctionWrapHandler) -> dict[str, Any]:
        """Drop only ``None`` keys — see ``keep_present``. Required fields are
        non-optional (never ``None``), so they are never dropped."""
        return keep_present(handler(self).items())
