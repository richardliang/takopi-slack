from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from takopi.api import ConfigError


@dataclass(frozen=True, slots=True)
class SlackTransportSettings:
    bot_token: str
    channel_id: str
    app_token: str
    message_overflow: Literal["trim", "split"] = "split"

    @classmethod
    def from_config(
        cls, config: object, *, config_path: Path
    ) -> "SlackTransportSettings":
        if isinstance(config, SlackTransportSettings):
            return config
        if not isinstance(config, dict):
            raise ConfigError(
                f"Invalid `transports.slack` in {config_path}; expected a table."
            )

        bot_token = _require_str(config, "bot_token", config_path=config_path)
        channel_id = _require_str(config, "channel_id", config_path=config_path)
        app_token = _require_str(config, "app_token", config_path=config_path)

        message_overflow = config.get("message_overflow", "split")
        if not isinstance(message_overflow, str):
            raise ConfigError(
                f"Invalid `transports.slack.message_overflow` in {config_path}; "
                "expected a string."
            )
        message_overflow = message_overflow.strip()
        if message_overflow not in {"trim", "split"}:
            raise ConfigError(
                f"Invalid `transports.slack.message_overflow` in {config_path}; "
                "expected 'trim' or 'split'."
            )

        return cls(
            bot_token=bot_token,
            channel_id=channel_id,
            app_token=app_token,
            message_overflow=message_overflow,
        )


def _require_str(config: dict[str, Any], key: str, *, config_path: Path) -> str:
    value = config.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(
            f"Invalid `transports.slack.{key}` in {config_path}; "
            "expected a non-empty string."
        )
    return value.strip()
