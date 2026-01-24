from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from takopi.transport import MessageRef, RenderedMessage, SendOptions


class FakeTransport:
    def __init__(self) -> None:
        self.send_calls: list[dict[str, Any]] = []
        self.edit_calls: list[dict[str, Any]] = []
        self.delete_calls: list[MessageRef] = []
        self._next_id = 1

    async def send(
        self,
        *,
        channel_id: int | str,
        message: RenderedMessage,
        options: SendOptions | None = None,
    ) -> MessageRef:
        ref = MessageRef(channel_id=channel_id, message_id=self._next_id)
        self._next_id += 1
        self.send_calls.append(
            {
                "channel_id": channel_id,
                "message": message,
                "options": options,
                "ref": ref,
            }
        )
        thread_id = options.thread_id if options is not None else None
        return MessageRef(
            channel_id=ref.channel_id,
            message_id=ref.message_id,
            thread_id=thread_id,
        )

    async def edit(
        self, *, ref: MessageRef, message: RenderedMessage, wait: bool = True
    ) -> MessageRef:
        self.edit_calls.append({"ref": ref, "message": message, "wait": wait})
        return ref

    async def delete(self, *, ref: MessageRef) -> bool:
        self.delete_calls.append(ref)
        return True

    async def close(self) -> None:
        return None


@dataclass(slots=True)
class FakeRuntime:
    allowlist: list[str] | None = None
    config_path: Any = None
    plugin_config_value: dict[str, Any] | None = None

    def plugin_config(self, command_id: str) -> dict[str, Any]:
        _ = command_id
        return self.plugin_config_value or {}
