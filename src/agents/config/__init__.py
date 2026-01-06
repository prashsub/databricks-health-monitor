"""Agent configuration module."""

from .settings import settings, AgentSettings
from .genie_spaces import (
    GENIE_SPACES,
    get_genie_space_id,
    get_genie_space_config,
    get_all_configured_spaces,
    validate_genie_spaces,
)

__all__ = [
    "settings",
    "AgentSettings",
    "GENIE_SPACES",
    "get_genie_space_id",
    "get_genie_space_config",
    "get_all_configured_spaces",
    "validate_genie_spaces",
]
