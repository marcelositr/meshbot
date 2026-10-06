# MeshBot

A modular bot for Meshtastic networks.

MeshBot is designed to run in two environments:

- **Development:** a local simulator that behaves like a small Meshtastic chat network.
- **Production:** communication with real Meshtastic devices through USB, Wi-Fi, or Bluetooth.

The bot core is intentionally independent from the transport and external services.

## Development

The default configuration is safe: it uses the local simulator and does not transmit over a real radio.

Install development dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Configure the simulator:

```bash
cp config/config.example.toml config/config.toml
```

Run the local simulator:

```bash
python3 -m meshbot
```

The simulator accepts messages such as:

```text
!12345678 !ping
!12345678 !tempo Ituverava
!12345678 !tempo Ituverava/SP
!12345678 !registrar
!12345678 !nome João da Silva
!12345678 !tempo Ituverava/SP
!12345678 !defesacivil Ituverava/SP
```

The `!tempo` command resolves municipalities through IBGE and accepts `Cidade/UF` for ambiguous names. Manual weather queries are sent privately to the requester. The weather service can also publish an automatic bulletin at the configured morning, afternoon, and night times; each bulletin is sent once during the configured minute plus a one-minute tolerance and uses the configured `weather.location` and `weather.recipient_id`. Automatic weather bulletins are disabled by default.

The `!defesacivil` command queries the official Defense Civil public alert feed for a municipality and reports the current active alerts. It is a read-only, on-demand query: each request is independent, and a previous response never suppresses a later query. CAP `Actual` alerts are considered, while `Update` and `Cancel` references are applied to the current feed before the response is built. Expired alerts are ignored. The response can be adapted through `defesa_civil.mode` (`normal`, `attention`, or `emergency`) and optional `show_*`, `max_alerts`, and `max_message_length` settings. The bot can also synchronize the official feed continuously and transmit only new or updated alerts matching the configured municipality. Automatic transmission is disabled by default and should be tested with the simulator before using a real radio.

The `!registrar` command registers the node that sent the message. A registered user can set or replace their friendly display name with `!nome <nome>`. User names accept Unicode letters, numbers, and spaces, preserve uppercase/lowercase, normalize surrounding/repeated spaces, and reject punctuation, symbols, and emojis. Names are limited to 24 characters.

A user can register their own node with `!registrar`. Moderation commands such as `!bloquear`, `!desbloquear`, and `!silenciar` require administrator privileges. Administrators cannot moderate other administrators. `!silenciar` accepts an optional duration in minutes and otherwise uses `default_silence_minutes`.

Run tests:

```bash
pytest
```

Check code quality:

```bash
ruff check .
mypy
```

## Configuration

Copy `config/config.example.toml` to `config/config.toml` and edit the documented settings.

The message interval and the morning/afternoon/night weather period boundaries are configurable so each network can choose its own operating behavior. Automatic weather bulletins can be enabled separately with `weather.automatic_enabled`, `weather.location`, and `weather.recipient_id`; when enabled, the worker sends one compact bulletin in each configured one-minute window and does not send a missed bulletin after the window has passed. Defense Civil presentation is also configurable so a network can keep responses compact in normal periods and expose more official alert context during attention or emergency periods.

The `admins` setting defines the initial administrators. Administrative rules are enforced by the application and are not configurable.

`config/config.toml` is intentionally ignored by Git because it may contain installation-specific settings and secrets.


## Production

For a real Meshtastic device, set `environment = "production"` and choose one of `usb`, `wifi`, or `bluetooth` as `transport`. Configure `device` when the selected interface needs an explicit device/address.

The production runtime supervises background workers, retries transient Defense Civil feed failures with bounded backoff, and performs a graceful shutdown of workers and the transport. The Meshtastic transport also reconnects after connection loss.

Automatic Defense Civil transmission requires:

```toml
[defesa_civil]
enabled = true
automatic_enabled = true
location = "Ribeirão Preto/SP"
recipient_id = "^all"
poll_interval_seconds = 300
```

Keep `automatic_enabled = false` until the radio transport and destination policy have been tested. The location filter currently uses the CAP area text; geometric CAP matching is a future refinement.

### systemd

An example user-service unit is provided at `deploy/meshbot.service.example`. Copy it to `~/.config/systemd/user/meshbot.service`, adjust `WorkingDirectory` and `ExecStart` if the installation path differs, then:

```bash
systemctl --user daemon-reload
systemctl --user enable --now meshbot.service
systemctl --user status meshbot.service
journalctl --user -u meshbot.service -f
```

The service is configured to restart after an unexpected process failure. Use `systemctl --user stop meshbot.service` for a normal shutdown.
