# Arquitetura

## Objetivo

O MeshBot deve permanecer dividido em quatro zonas:

~~~text
Interfaces
    |
    v
Application
    |
    v
Domain

Infrastructure implementa portas e integrações externas.
~~~

A dependência deve apontar para dentro.

## Domain

Atualmente contém mensagens, usuário, papéis, validação de node ID, validação de nome e estado de silenciamento.

O domínio deve permanecer pequeno, determinístico e independente de infraestrutura.

## Application

Contém autorização, orquestração, comandos, usuários, moderação, tempo, Defesa Civil e portas.

A aplicação representa casos de uso e políticas.

## Infrastructure

Contém simulador, SQLite, IBGE, INMET, feed CAP e implementações fake.

Dependências externas ficam aqui.

## Interfaces

A CLI é hoje o composition root.

Quando existir transporte real, ele deve ser conectado aqui. O caso de uso não escolhe o transporte.

## Fluxo de mensagem

~~~text
Transport
   |
IncomingMessage
   |
AuthorizationPolicy
   |
CommandHandler
   |
Command
   |
Application Service
   |
Infrastructure adapter
   |
OutgoingMessage
   |
Transport
~~~

Nenhum comando deve abrir banco ou chamar HTTP diretamente.

## Fluxo de serviços

Tempo:

~~~text
!tempo Cidade/UF
      |
TempoCommand
      |
WeatherService
      |
IBGE -> INMET
~~~

Defesa Civil atual:

~~~text
!defesacivil Cidade/UF
      |
DefenseCivilCommand
      |
DefenseCivilService
      |
IBGE + CAP/XML
~~~

Defesa Civil futura:

~~~text
CAP
 |
Fetcher
 |
Parser
 |
Normalizer
 |
Geographic Matcher
 |
State Store
 |
Deduplication/Event Engine
 |
Formatter
 |
MeshtasticTransport
~~~

## Composition root

A composição futura deve ser explícita:

~~~text
development -> SimulatorTransport
production  -> MeshtasticTransport
~~~

O núcleo não pode saber qual transporte está em uso.

## Portas futuras

Devem ser avaliadas para:

- transporte;
- persistência de usuários;
- relógio;
- resolução de município;
- previsão do tempo;
- feed de alertas;
- estado de alertas;
- localização;
- observabilidade.

Uma porta deve existir quando uma dependência externa ameaça a testabilidade ou a reutilização do caso de uso.

## O que não fazer

Não colocar HTTP ou SQL no domínio. Não colocar código Meshtastic no MeshBot. Não colocar regras de autorização no simulador. Não colocar CAP na CLI.

Também não criar abstrações apenas por estética. A abstração precisa proteger uma fronteira real.

## Perguntas obrigatórias antes de uma nova feature

1. Qual é o caso de uso?
2. Qual regra pertence ao domínio?
3. Qual dependência é externa?
4. Qual porta a isola?
5. Como testar sem hardware e rede?
6. Qual comportamento de falha existe?
7. Como a configuração controla o comportamento?
8. Como o operador saberá que está funcionando?
