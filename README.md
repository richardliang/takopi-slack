# takopi-slack-plugin

Slack transport plugin for Takopi. Uses Slack socket connections only, and
responds in a single channel or DM.

## Requirements

- Python 3.14+
- takopi >=0.20.0
- Slack bot token with `chat:write`
- Slack app token (`xapp-`) with `connections:write`

## Install

Install into the same Python environment as Takopi.

Using uv tool installs:

```sh
uv tool install -U takopi --with takopi-slack-plugin
```

Using a virtualenv:

```sh
pip install takopi-slack-plugin
```

## Configure

Add to your `~/.takopi/takopi.toml`:

```toml
transport = "slack"

[transports.slack]
bot_token = "xoxb-..."
app_token = "xapp-..."
channel_id = "C12345678"
```

### Required Directives

Slack messages must include both a project and worktree directive in the
first line. Messages that do not match are ignored.

Example:

```
@takopi /zkp2p-clients @feat/web/monad-usdt0 add a retry to the API call
```

### Socket Connections (required)

Enable Slack socket connections in your app and create an app-level token with
`connections:write`, then configure:

```toml
[transports.slack]
bot_token = "xoxb-..."
app_token = "xapp-..."
channel_id = "C12345678"
```

Enable Slack events for `message.channels`, `message.groups`, `message.im`,
`message.mpim`, and/or `app_mention`, depending on your channel type.

### Thread Sessions

Takopi always replies in threads and stores resume tokens per thread at
`~/.takopi/slack_thread_sessions_state.json`.

If you use a plugin allowlist, enable this distribution:

```toml
[plugins]
enabled = ["takopi-slack-plugin"]
```

## Start

Run Takopi with the Slack transport:

```sh
takopi --transport slack
```

If you already set `transport = "slack"` in the config, `takopi` is enough.

Optional interactive setup:

```sh
takopi --onboard --transport slack
```
