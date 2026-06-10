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
    many). Serialized output is pruned of values indistinguishable from absence
    (see ``_drop_empty``) to keep MCP responses compact.
    """

    model_config = ConfigDict(populate_by_name=True)

    @model_serializer(mode="wrap")
    def _drop_empty(self, handler: SerializerFunctionWrapHandler) -> dict[str, Any]:
        """Drop keys whose value conveys nothing absence wouldn't — ``None``,
        ``""``, and ``{}`` — keeping the output a token-lean subset of the
        (all-optional) schema. Kept: ``[]`` (signals "no results") and ``0`` /
        ``False`` (definite states). Runs bottom-up via the wrap handler, so a
        submodel that prunes to ``{}`` is then dropped by its parent — empty
        subtrees collapse away recursively."""
        return {
            k: v
            for k, v in handler(self).items()
            if v is not None and v != "" and v != {}
        }
