from pathlib import Path

import pytest

from takopi.api import ResumeToken, RunContext
from takopi_slack_plugin.thread_sessions import SlackThreadSessionStore


@pytest.mark.anyio
async def test_thread_sessions_resume_roundtrip(tmp_path) -> None:
    path = tmp_path / "slack_thread_sessions_state.json"
    store = SlackThreadSessionStore(path)

    await store.set_resume(
        channel_id="C1",
        thread_id="T1",
        token=ResumeToken(engine="codex", value="abc"),
    )
    assert await store.get_resume(
        channel_id="C1", thread_id="T1", engine="codex"
    ) == ResumeToken(engine="codex", value="abc")

    store2 = SlackThreadSessionStore(path)
    assert await store2.get_resume(
        channel_id="C1", thread_id="T1", engine="codex"
    ) == ResumeToken(engine="codex", value="abc")


@pytest.mark.anyio
async def test_thread_sessions_context_and_overrides(tmp_path) -> None:
    path = tmp_path / "slack_thread_sessions_state.json"
    store = SlackThreadSessionStore(path)

    context = RunContext(project="proj", branch="feat")
    await store.set_context(channel_id="C1", thread_id="T1", context=context)
    assert await store.get_context(channel_id="C1", thread_id="T1") == context

    await store.set_default_engine(
        channel_id="C1", thread_id="T1", engine="  codex  "
    )
    assert await store.get_default_engine(channel_id="C1", thread_id="T1") == "codex"

    await store.set_model_override(
        channel_id="C1", thread_id="T1", engine="codex", model=" gpt-4o "
    )
    await store.set_reasoning_override(
        channel_id="C1", thread_id="T1", engine="codex", level=" high "
    )
    assert await store.get_model_override(
        channel_id="C1", thread_id="T1", engine="codex"
    ) == "gpt-4o"
    assert await store.get_reasoning_override(
        channel_id="C1", thread_id="T1", engine="codex"
    ) == "high"

    await store.set_model_override(
        channel_id="C1", thread_id="T1", engine="codex", model=None
    )
    await store.set_reasoning_override(
        channel_id="C1", thread_id="T1", engine="codex", level=None
    )
    assert await store.get_model_override(
        channel_id="C1", thread_id="T1", engine="codex"
    ) is None
    assert await store.get_reasoning_override(
        channel_id="C1", thread_id="T1", engine="codex"
    ) is None


@pytest.mark.anyio
async def test_thread_sessions_clear_and_state(tmp_path) -> None:
    path = tmp_path / "slack_thread_sessions_state.json"
    store = SlackThreadSessionStore(path)

    await store.set_resume(
        channel_id="C1",
        thread_id="T1",
        token=ResumeToken(engine="codex", value="one"),
    )
    await store.set_context(
        channel_id="C1", thread_id="T1", context=RunContext(project="proj")
    )

    state = await store.get_state(channel_id="C1", thread_id="T1")
    assert state and state["context"]["project"] == "proj"

    await store.clear_resumes(channel_id="C1", thread_id="T1")
    assert await store.get_resume(
        channel_id="C1", thread_id="T1", engine="codex"
    ) is None

    await store.clear_thread(channel_id="C1", thread_id="T1")
    assert await store.get_context(channel_id="C1", thread_id="T1") is None
