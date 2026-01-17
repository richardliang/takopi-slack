from __future__ import annotations

from pathlib import Path

import msgspec

from takopi.api import ResumeToken, get_logger
from takopi.telegram.state_store import JsonStateStore

logger = get_logger(__name__)

STATE_VERSION = 1
STATE_FILENAME = "slack_thread_sessions_state.json"


class _ThreadSession(msgspec.Struct, forbid_unknown_fields=False):
    resumes: dict[str, str] = msgspec.field(default_factory=dict)


class _ThreadSessionsState(msgspec.Struct, forbid_unknown_fields=False):
    version: int
    threads: dict[str, _ThreadSession] = msgspec.field(default_factory=dict)


def resolve_sessions_path(config_path: Path) -> Path:
    return config_path.with_name(STATE_FILENAME)


def _thread_key(channel_id: str, thread_id: str) -> str:
    return f"{channel_id}:{thread_id}"


def _new_state() -> _ThreadSessionsState:
    return _ThreadSessionsState(version=STATE_VERSION, threads={})


class SlackThreadSessionStore(JsonStateStore[_ThreadSessionsState]):
    def __init__(self, path: Path) -> None:
        super().__init__(
            path,
            version=STATE_VERSION,
            state_type=_ThreadSessionsState,
            state_factory=_new_state,
            log_prefix="slack.thread_sessions",
            logger=logger,
        )

    async def get_resume(
        self, *, channel_id: str, thread_id: str, engine: str
    ) -> ResumeToken | None:
        key = _thread_key(channel_id, thread_id)
        async with self._lock:
            self._reload_locked_if_needed()
            session = self._state.threads.get(key)
            if session is None:
                return None
            value = session.resumes.get(engine)
            if not value:
                return None
            return ResumeToken(engine=engine, value=value)

    async def set_resume(
        self, *, channel_id: str, thread_id: str, token: ResumeToken
    ) -> None:
        key = _thread_key(channel_id, thread_id)
        async with self._lock:
            self._reload_locked_if_needed()
            session = self._state.threads.get(key)
            if session is None:
                session = _ThreadSession()
                self._state.threads[key] = session
            session.resumes[token.engine] = token.value
            self._save_locked()

    async def clear_thread(self, *, channel_id: str, thread_id: str) -> None:
        key = _thread_key(channel_id, thread_id)
        async with self._lock:
            self._reload_locked_if_needed()
            if key not in self._state.threads:
                return
            self._state.threads.pop(key, None)
            self._save_locked()
