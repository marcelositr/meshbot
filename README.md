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
!12345678 /ping
!12345678 /tempo Ituverava
```

The `/tempo` command resolves the municipality by name, accepts `Cidade - UF` for ambiguous names, and supports `/tempo ibge <codigo>` as a fallback.

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

`config/config.toml` is intentionally ignored by Git because it may contain installation-specific settings and secrets.
