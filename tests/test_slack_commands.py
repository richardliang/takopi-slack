from __future__ import annotations

import types

import pytest

from takopi.commands import CommandResult
from takopi.config import ConfigError
from takopi.runner_bridge import ExecBridgeConfig
from takopi.transport import MessageRef
from takopi_slack_plugin.commands.dispatch import dispatch_command
from tests.slack_fakes import FakeRuntime, FakeTransport


class _Backend:
    id = "hello"
    description = "hello"

    async def handle(self, ctx):
        _ = ctx
        return CommandResult(text="ok", notify=True)


@pytest.mark.anyio
async def test_dispatch_command_sends_result(monkeypatch) -> None:
    transport = FakeTransport()
    runtime = FakeRuntime()
    exec_cfg = ExecBridgeConfig(transport=transport, presenter=object(), final_notify=False)
    cfg = types.SimpleNamespace(runtime=runtime, exec_cfg=exec_cfg)

    monkeypatch.setattr(
        "takopi_slack_plugin.commands.dispatch.get_command",
        lambda *args, **kwargs: _Backend(),
    )

    handled = await dispatch_command(
        cfg,
        command_id="hello",
        args_text="",
        full_text="/hello",
        channel_id="C1",
        message_id="1",
        thread_id=None,
        reply_ref=None,
        reply_text=None,
        running_tasks={},
        on_thread_known=None,
        default_engine_override=None,
        default_context=None,
        engine_overrides_resolver=None,
    )

    assert handled is True
    assert transport.send_calls[0]["message"].text == "ok"


@pytest.mark.anyio
async def test_dispatch_command_handles_config_error(monkeypatch) -> None:
    transport = FakeTransport()
    runtime = FakeRuntime()
    exec_cfg = ExecBridgeConfig(transport=transport, presenter=object(), final_notify=False)
    cfg = types.SimpleNamespace(runtime=runtime, exec_cfg=exec_cfg)

    def _raise(*_args, **_kwargs):
        raise ConfigError("boom")

    monkeypatch.setattr("takopi_slack_plugin.commands.dispatch.get_command", _raise)

    handled = await dispatch_command(
        cfg,
        command_id="hello",
        args_text="",
        full_text="/hello",
        channel_id="C1",
        message_id="1",
        thread_id=None,
        reply_ref=MessageRef(channel_id="C1", message_id="1"),
        reply_text=None,
        running_tasks={},
        on_thread_known=None,
        default_engine_override=None,
        default_context=None,
        engine_overrides_resolver=None,
    )

    assert handled is True
    assert transport.send_calls[0]["message"].text.startswith("error:")


@pytest.mark.anyio
async def test_dispatch_command_returns_false_for_missing(monkeypatch) -> None:
    transport = FakeTransport()
    runtime = FakeRuntime()
    exec_cfg = ExecBridgeConfig(transport=transport, presenter=object(), final_notify=False)
    cfg = types.SimpleNamespace(runtime=runtime, exec_cfg=exec_cfg)

    monkeypatch.setattr(
        "takopi_slack_plugin.commands.dispatch.get_command",
        lambda *args, **kwargs: None,
    )

    handled = await dispatch_command(
        cfg,
        command_id="hello",
        args_text="",
        full_text="/hello",
        channel_id="C1",
        message_id="1",
        thread_id=None,
        reply_ref=None,
        reply_text=None,
        running_tasks={},
        on_thread_known=None,
        default_engine_override=None,
        default_context=None,
        engine_overrides_resolver=None,
    )

    assert handled is False
    assert transport.send_calls == []


@pytest.mark.anyio
async def test_dispatch_command_sends_error_on_backend_failure(monkeypatch) -> None:
    transport = FakeTransport()
    runtime = FakeRuntime()
    exec_cfg = ExecBridgeConfig(transport=transport, presenter=object(), final_notify=False)
    cfg = types.SimpleNamespace(runtime=runtime, exec_cfg=exec_cfg)

    class _BadBackend:
        id = "bad"
        description = "bad"

        async def handle(self, ctx):
            _ = ctx
            raise RuntimeError("nope")

    monkeypatch.setattr(
        "takopi_slack_plugin.commands.dispatch.get_command",
        lambda *args, **kwargs: _BadBackend(),
    )

    handled = await dispatch_command(
        cfg,
        command_id="bad",
        args_text="",
        full_text="/bad",
        channel_id="C1",
        message_id="1",
        thread_id=None,
        reply_ref=None,
        reply_text=None,
        running_tasks={},
        on_thread_known=None,
        default_engine_override=None,
        default_context=None,
        engine_overrides_resolver=None,
    )

    assert handled is True
    assert transport.send_calls[0]["message"].text.startswith("error:")
