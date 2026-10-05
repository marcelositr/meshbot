# MeshBot

A modular bot for Meshtastic networks.

MeshBot is designed to run in two environments:

- **Development:** a local simulator that behaves like a small Meshtastic chat network.
- **Production:** communication with real Meshtastic devices through supported transports.

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
!12345678 !registrar !22222222
!12345678 !bloquear !22222222
!12345678 !desbloquear !22222222
!12345678 !silenciar !22222222 30
```

The `!tempo` command resolves municipalities through IBGE, accepts `Cidade/UF` for ambiguous names, and supports `!tempo ibge <codigo>` as a fallback.

The `!registrar` command uses `!registrar <node_id>`. A registered user can set or replace their friendly display name with `!nome <nome>`. User names accept Unicode letters, numbers, and spaces, preserve uppercase/lowercase, normalize surrounding/repeated spaces, and reject punctuation, symbols, and emojis. Names are limited to 24 characters.

The `!registrar`, `!bloquear`, `!desbloquear`, and `!silenciar` commands are restricted to administrators. Administrators cannot moderate other administrators. `!silenciar` accepts an optional duration in minutes and otherwise uses `default_silence_minutes`.

Run tests:

```bash
pytest
```

Check code quality:

```bash
ruff check .
mypy src
```

## Configuration

Copy `config/config.example.toml` to `config/config.toml` and edit the documented settings.

The message interval and the morning/afternoon/night weather period boundaries are configurable so each network can choose its own operating behavior.

The `admins` setting defines the initial administrators. Administrative rules are enforced by the application and are not configurable.

`config/config.toml` is intentionally ignored by Git because it may contain installation-specific settings and secrets.
