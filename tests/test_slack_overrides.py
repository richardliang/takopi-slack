from takopi_slack_plugin.overrides import is_valid_reasoning_level, supports_reasoning


def test_supports_reasoning() -> None:
    assert supports_reasoning("codex") is True
    assert supports_reasoning("claude") is False


def test_reasoning_levels() -> None:
    assert is_valid_reasoning_level("low") is True
    assert is_valid_reasoning_level("extreme") is False
