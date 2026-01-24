import pytest

from takopi_slack_plugin.commands.file_transfer import SlackFile
from takopi_slack_plugin.voice import transcribe_voice


class _FakeClient:
    async def download_file(self, *, url: str):
        _ = url
        return b"audio"


@pytest.mark.anyio
async def test_transcribe_voice_disabled() -> None:
    messages: list[str] = []

    async def reply(*, text: str) -> None:
        messages.append(text)

    result = await transcribe_voice(
        client=_FakeClient(),
        file=SlackFile(
            file_id="F1",
            name="voice.ogg",
            size=10,
            mimetype="audio/ogg",
            filetype="ogg",
            url_private="https://example.com",
            url_private_download=None,
            mode=None,
        ),
        enabled=False,
        model="gpt-4o-mini-transcribe",
        reply=reply,
    )
    assert result is None
    assert messages
