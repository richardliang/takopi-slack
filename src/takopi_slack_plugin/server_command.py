from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from takopi.api import (
    CommandBackend,
    CommandContext,
    CommandResult,
    ConfigError,
    HOME_CONFIG_PATH,
    RunContext,
    RunRequest,
)

DEFAULT_HOST = "127.0.0.1"

DEV_SERVER_START_PROMPT = (
    "You are operating within a Takopi worktree context.\n"
    "\n"
    "Goal: ensure the correct dev server is running.\n"
    "\n"
    "Target:\n"
    "- host: {host}\n"
    "- port: {port}\n"
    "\n"
    "Rules:\n"
    "- If something is already listening on the target port, confirm it is the "
    "correct dev server and leave it running.\n"
    "- If nothing is listening, find the right dev command from README, "
    "AGENTS, or package scripts and start it.\n"
    "- Prefer the repo's primary toolchain (pnpm > bun > npm > yarn; "
    "uv > poetry > pip for Python).\n"
    "- Install dependencies only if required to start the dev server.\n"
    "- Bind to the target host and port; avoid public binds unless required.\n"
    "\n"
    "Edge cases:\n"
    "- Monorepo with multiple apps: pick the app for this context and say which.\n"
    "- If the default port differs, override it to {port} or explain why you "
    "cannot.\n"
    "- If startup fails, report the error and the next step.\n"
    "\n"
    "Context: {context_line}\n"
    "Worktree: {worktree}\n"
)

DEV_SERVER_STOP_PROMPT = (
    "You are operating within a Takopi worktree context.\n"
    "\n"
    "Goal: stop the dev server if it is still listening on port {port}.\n"
    "\n"
    "Rules:\n"
    "- If nothing is listening on the port, do nothing.\n"
    "- Prefer a graceful stop (repo stop command or SIGTERM).\n"
    "- Report what you stopped or why it could not be stopped.\n"
    "\n"
    "Context: {context_line}\n"
    "Worktree: {worktree}\n"
)


@dataclass(frozen=True, slots=True)
class ServerConfig:
    host: str
    start_port: int | None
    start_instruction: str | None
    stop_instruction: str | None

    @classmethod
    def from_config(cls, config: object, *, config_path: Path) -> "ServerConfig":
        if isinstance(config, ServerConfig):
            return config
        if not isinstance(config, dict):
            raise ConfigError(
                f"Invalid `server` config in {config_path}; expected a table."
            )

        host = _optional_str(config, "host", config_path=config_path) or DEFAULT_HOST
        start_port = _optional_int(config, "start_port", config_path=config_path)
        if start_port is not None:
            _validate_port(start_port, config_path=config_path)
        start_instruction = _optional_str(
            config, "start_instruction", config_path=config_path
        )
        if start_instruction is not None:
            start_instruction = start_instruction.strip() or None
        stop_instruction = _optional_str(
            config, "stop_instruction", config_path=config_path
        )
        if stop_instruction is not None:
            stop_instruction = stop_instruction.strip() or None

        return cls(
            host=host,
            start_port=start_port,
            start_instruction=start_instruction,
            stop_instruction=stop_instruction,
        )


@dataclass(frozen=True, slots=True)
class PromptContext:
    context_line: str | None
    cwd: Path | None


class ServerCommand:
    id = "server"
    description = "Start/stop dev servers (LLM shortcut)"

    async def handle(self, ctx: CommandContext) -> CommandResult | None:
        if not ctx.args:
            return CommandResult(text=_help_text())

        ambient_context = getattr(ctx.executor, "default_context", None)
        resolved = ctx.runtime.resolve_message(
            text=ctx.text,
            reply_text=ctx.reply_text,
            ambient_context=ambient_context,
            chat_id=_coerce_chat_id(ctx.message.channel_id),
        )
        context = resolved.context
        context_line = ctx.runtime.format_context_line(context)
        cwd = ctx.runtime.resolve_run_cwd(context)

        config = _load_config(ctx, context)

        action = ctx.args[0].lower()
        if action in {"start", "up"}:
            port, instruction = _parse_action_args(
                ctx.args[1:], default_port=config.start_port
            )
            instruction = instruction or config.start_instruction
            prompt = _build_start_prompt(
                host=config.host,
                port=port,
                prompt_context=PromptContext(context_line=context_line, cwd=cwd),
                instruction=instruction,
            )
            await ctx.executor.run_one(
                RunRequest(prompt=prompt, context=_as_run_context(context))
            )
            return None
        if action in {"stop", "down"}:
            port, instruction = _parse_action_args(
                ctx.args[1:], default_port=config.start_port
            )
            instruction = instruction or config.stop_instruction
            prompt = _build_stop_prompt(
                port=port,
                prompt_context=PromptContext(context_line=context_line, cwd=cwd),
                instruction=instruction,
            )
            await ctx.executor.run_one(
                RunRequest(prompt=prompt, context=_as_run_context(context))
            )
            return None

        return CommandResult(text=_help_text())


def _help_text() -> str:
    return "usage: `/server start [port] [instruction...]` or `/server stop [port] [instruction...]`"


def _coerce_chat_id(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    return None


def _context_project(context: object | None) -> str | None:
    if isinstance(context, RunContext):
        return context.project
    return None


def _as_run_context(context: object | None) -> RunContext | None:
    if isinstance(context, RunContext):
        return context
    project = _context_project(context)
    if project is None:
        return None
    return RunContext(project=project)


def _load_config(ctx: CommandContext, context: object | None) -> ServerConfig:
    base = dict(ctx.plugin_config or {})
    project_override: dict[str, Any] = {}
    config_path = ctx.config_path or HOME_CONFIG_PATH
    project = _context_project(context)
    if project:
        project_override = _project_override(base, project, config_path=config_path)
    merged = _merge_config(base, project_override)
    return ServerConfig.from_config(merged, config_path=config_path)


def _project_override(
    config: dict[str, Any],
    project: str,
    *,
    config_path: Path,
) -> dict[str, Any]:
    overrides = config.get("projects")
    if overrides is None:
        return {}
    if not isinstance(overrides, dict):
        raise ConfigError(
            f"Invalid `plugins.server.projects` in {config_path}; expected a table."
        )
    raw = overrides.get(project) or overrides.get(project.lower())
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ConfigError(
            f"Invalid `plugins.server.projects.{project}` in {config_path}; "
            "expected a table."
        )
    return dict(raw)


def _merge_config(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    if not override:
        return base
    merged = dict(base)
    merged.update(override)
    return merged


def _optional_str(config: dict[str, Any], key: str, *, config_path: Path) -> str | None:
    if key not in config:
        return None
    value = config.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ConfigError(
            f"Invalid `server.{key}` in {config_path}; expected a string."
        )
    return value.strip()


def _optional_int(config: dict[str, Any], key: str, *, config_path: Path) -> int | None:
    if key not in config:
        return None
    value = config.get(key)
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    raise ConfigError(f"Invalid `server.{key}` in {config_path}; expected an integer.")


def _parse_port(value: str) -> int | None:
    if value.isdigit():
        return int(value)
    if ":" in value:
        tail = value.rsplit(":", 1)[-1]
        if tail.isdigit():
            return int(tail)
    return None


def _parse_action_args(
    args: tuple[str, ...], *, default_port: int | None
) -> tuple[int, str | None]:
    if not args:
        if default_port is None:
            raise ConfigError(_help_text())
        return default_port, None
    parsed = _parse_port(args[0])
    if parsed is not None:
        instruction = " ".join(args[1:]).strip() or None
        return parsed, instruction
    if default_port is None:
        raise ConfigError(_help_text())
    instruction = " ".join(args).strip() or None
    return default_port, instruction


def _validate_port(port: int, *, config_path: Path) -> None:
    if not (1024 <= port <= 65535):
        raise ConfigError(
            f"Invalid `server.start_port` in {config_path}; expected 1024-65535."
        )


def _format_prompt_context(prompt_context: PromptContext) -> str:
    return prompt_context.context_line or "none"


def _format_prompt_worktree(prompt_context: PromptContext) -> str:
    if prompt_context.cwd is not None:
        return str(prompt_context.cwd)
    return "unknown"


def _build_start_prompt(
    *,
    host: str,
    port: int,
    prompt_context: PromptContext,
    instruction: str | None,
) -> str:
    prompt = DEV_SERVER_START_PROMPT.format(
        host=host,
        port=port,
        context_line=_format_prompt_context(prompt_context),
        worktree=_format_prompt_worktree(prompt_context),
    )
    if instruction:
        prompt = f"{prompt}\nUser instruction: {instruction}\n"
    return prompt


def _build_stop_prompt(
    *,
    port: int,
    prompt_context: PromptContext,
    instruction: str | None,
) -> str:
    prompt = DEV_SERVER_STOP_PROMPT.format(
        port=port,
        context_line=_format_prompt_context(prompt_context),
        worktree=_format_prompt_worktree(prompt_context),
    )
    if instruction:
        prompt = f"{prompt}\nUser instruction: {instruction}\n"
    return prompt


BACKEND: CommandBackend = ServerCommand()
