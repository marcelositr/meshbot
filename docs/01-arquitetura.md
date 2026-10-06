# Arquitetura

## Objetivo

Manter o núcleo independente de Meshtastic, HTTP, SQLite e terminal.

A estrutura atual é:

```text
src/meshbot/
├── domain/
├── application/
├── infrastructure/
└── interfaces/
```

A dependência conceitual aponta para dentro:

```text
interfaces
    ↓
application
    ↓
domain

infrastructure implementa contratos usados pela application.
```

## Domain

Responsável por dados e regras pequenas e determinísticas.

Atualmente:

- mensagens;
- usuário;
- papéis;
- validação de node ID;
- normalização/validação de nome;
- estado de silenciamento.

O domínio não conhece Meshtastic, HTTP, TOML, SQLite ou curses.

## Application

Contém os casos de uso e políticas:

- `MeshBot`;
- autorização;
- usuários;
- moderação;
- comandos;
- tempo;
- boletim automático;
- Defesa Civil;
- estado de alertas;
- entrega e polling;
- runtime;
- logging;
- portas.

A aplicação recebe dependências por construtores e protocolos sempre que uma fronteira externa precisa ser substituída em testes.

## Infrastructure

Implementa integrações externas:

- `SimulatorTransport`;
- `MeshtasticTransport`;
- SQLite de usuários;
- SQLite de alertas;
- IBGE;
- INMET;
- feed CAP da Defesa Civil;
- fakes para testes.

## Interfaces

A CLI é o composition root.

Ela:

1. carrega configuração;
2. configura logging;
3. inicializa repositórios;
4. promove administradores configurados;
5. cria serviços;
6. cria workers opcionais;
7. compõe comandos de acordo com `[features]`;
8. cria o bot;
9. escolhe simulador/TUI ou runtime de produção conforme o transporte configurado.

O núcleo não escolhe seu próprio transporte.

## Fluxo de mensagem

```text
Transport
   ↓
IncomingMessage
   ↓
AuthorizationPolicy
   ↓
CommandHandler
   ↓
Command
   ↓
Application service
   ↓
OutgoingMessage
   ↓
Transport
```

O atraso entre respostas é responsabilidade do `MeshBot`, não do comando.

## Fluxo de tempo

```text
!tempo Cidade/UF
      ↓
TempoCommand
      ↓
WeatherService
      ↓
IBGECityResolver + INMET
      ↓
WeatherForecast
      ↓
OutgoingMessage[]
```

## Fluxo de Defesa Civil sob demanda

```text
!defesacivil Cidade/UF
      ↓
DefenseCivilCommand
      ↓
DefenseCivilAlertService
      ↓
IBGE + CAP/XML
      ↓
DefenseCivilAlert[]
      ↓
formatação + fragmentação
      ↓
OutgoingMessage[]
```

## Fluxo automático de Defesa Civil

```text
CAP
 ↓
DefenseCivilAlertService.get_all_alerts()
 ↓
DefenseCivilPoller
 ↓
DefenseCivilStateService
 ↓
new / updated / deactivated
 ↓
DefenseCivilEventDispatcher
 ↓
DefenseCivilDelivery
 ↓
formatter + localização textual
 ↓
MeshtasticTransport
```

O evento `deactivated` atualmente não transmite nada.

## Fluxo automático de tempo

```text
relógio
 ↓
WeatherBulletinWorker
 ↓
WeatherService
 ↓
WeatherForecast
 ↓
OutgoingMessage
 ↓
Transport
```

Cada janela configurada gera no máximo um boletim por dia.

## Transporte Meshtastic

O transporte real fica isolado atrás de `MessageTransport`.

A biblioteca Meshtastic é usada somente em `infrastructure/meshtastic_transport.py`.

O restante da aplicação trabalha apenas com:

- `IncomingMessage`;
- `OutgoingMessage`;
- `MessageTransport`.

Isso permite testar a aplicação sem rádio.

## Reconexão

A perda de conexão inicia um thread de reconexão dedicado.

O transporte:

1. marca-se desconectado;
2. espera o atraso inicial;
3. fecha a interface antiga;
4. cria uma nova interface;
5. aguarda confirmação de conexão;
6. aumenta o atraso em caso de falha;
7. limita o atraso máximo;
8. repete até reconectar ou ser fechado.

## Persistência

Há duas áreas SQLite separadas logicamente dentro do mesmo arquivo configurado:

- `users`;
- `defense_civil_alerts`.

A tabela de alertas não deve ser confundida com usuários.

Cada chamada ao repositório abre sua própria conexão SQLite.

## Composition root e configuração

A composição não usa uma fábrica genérica de plugins. Os recursos são simples o suficiente para permanecer explícitos.

Os toggles opcionais são aplicados na CLI:

```text
features.ping
features.weather_command
features.weather_bulletin
features.defense_civil_command
features.defense_civil_monitor
```

Isso evita registrar comandos ou workers desnecessários.

## Fronteiras ainda desejáveis

Não são tarefas automáticas; devem ser criadas somente quando houver necessidade real:

- relógio injetável onde testes temporais ficarem difíceis;
- localização/GPS;
- geometria CAP;
- outbox de transmissão;
- health/status;
- métricas externas.

Não criar uma abstração apenas porque ela parece arquiteturalmente elegante.

## Regras arquiteturais

- HTTP não entra no domínio.
- SQL não entra no domínio.
- Meshtastic não entra no domínio.
- curses não entra na aplicação.
- regras de autorização não ficam no simulador.
- CAP não fica na CLI.
- comandos não abrem banco diretamente.
- integrações externas devem ser testáveis sem depender da rede real.

