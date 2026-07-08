"""Base model for Slack schemas."""

from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    SerializerFunctionWrapHandler,
    model_serializer,
)


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
        """Drop only ``None`` keys — absence. Every present value, empty ones
        included (``""``, ``{}``, ``[]``, ``0``, ``False``), is kept: "present
        but empty" is distinct from absent. Required fields are non-optional
        (never ``None``), so they are never dropped."""
        return {k: v for k, v in handler(self).items() if v is not None}
