from __future__ import annotations

from dataclasses import dataclass

REASONING_LEVELS = frozenset({"minimal", "low", "medium", "high", "xhigh"})
REASONING_ENGINES = frozenset({"codex"})


@dataclass(frozen=True, slots=True)
class ResolvedOverrides:
    model: str | None = None
    reasoning: str | None = None


def supports_reasoning(engine_id: str) -> bool:
    return engine_id in REASONING_ENGINES


def is_valid_reasoning_level(level: str) -> bool:
    return level in REASONING_LEVELS
