# MeshBot

Bot modular para redes Meshtastic.

O MeshBot separa o núcleo da aplicação do transporte e das integrações externas. Pode ser executado localmente com um simulador ou conectado a um dispositivo Meshtastic real.

## Estado

O núcleo funcional está implementado.

O transporte Meshtastic suporta:

- USB
- Wi-Fi
- Bluetooth
- reconexão

Também existem comandos de tempo e Defesa Civil, automações, persistência SQLite, moderação, runtime de produção e uma TUI para desenvolvimento.

A validação com hardware real ainda é uma etapa pendente.

## Desenvolvimento

Crie o ambiente e instale as dependências:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp config/config.example.toml config/config.toml
```

Execute o simulador:

```bash
python3 -m meshbot
```

O simulador permite testar comandos sem transmitir por rádio.

## Configuração

A configuração de exemplo está em:

config/config.example.toml

A documentação completa está em [docs/](docs/).

Principais documentos:

- [Estado atual](docs/00-estado-atual.md)
- [Arquitetura](docs/01-arquitetura.md)
- [Contratos e regras](docs/02-contratos.md)
- [Operação e configuração](docs/03-operacao.md)
- [Qualidade e testes](docs/04-qualidade.md)
- [Defesa Civil](docs/05-defesa-civil.md)
- [Roadmap](docs/06-roadmap.md)

## Qualidade

Execute:

```bash
pytest -q
ruff check .
mypy
```

## Produção

Para usar um dispositivo real, configure o transporte desejado:

```toml
transport = "usb"
```

Os detalhes de instalação, transporte, runtime e systemd estão em [docs/03-operacao.md](docs/03-operacao.md).

## Roadmap

O próximo grande passo é a **validação do transporte com hardware Meshtastic real**.

As próximas etapas e decisões do projeto estão registradas em [docs/06-roadmap.md](docs/06-roadmap.md).

---

O objetivo do projeto é crescer de forma simples e testável, adicionando complexidade somente quando houver uma necessidade real.
