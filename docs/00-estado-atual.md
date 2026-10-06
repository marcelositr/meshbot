# Estado atual

## Resumo executivo

O MeshBot possui um núcleo de aplicação funcional, mas ainda não é um gateway Meshtastic de produção.

Hoje o fluxo completo entrada -> autorização -> comando -> serviço -> resposta funciona com o simulador. Usuários e moderação possuem persistência SQLite. Tempo e Defesa Civil possuem integrações externas reais.

A principal lacuna estrutural agora está no ciclo de vida operacional: os adaptadores Meshtastic já existem e recebem/enviam mensagens, mas ainda falta reconexão, supervisão e observabilidade de produção.

## O que existe

### Núcleo

- IncomingMessage e OutgoingMessage.
- MessageTransport como contrato.
- MeshBot como orquestrador.
- CommandHandler.
- AuthorizationPolicy.
- atraso entre mensagens.

### Usuários

- node ID no formato ! + 8 hexadecimais;
- cadastro pelo próprio usuário;
- nome amigável;
- normalização NFC;
- espaços duplicados reduzidos;
- letras Unicode e acentos;
- dígitos;
- preservação de caixa;
- rejeição de pontuação, símbolos e emojis;
- máximo de 24 caracteres;
- papéis user e admin.

### Moderação

- bloquear;
- desbloquear;
- silenciar temporariamente;
- duração padrão;
- proteção admin contra admin;
- notificações;
- nomes amigáveis nas notificações.

### Persistência

SQLite local com users contendo node_id, name, role, blocked e silenced_until.

Existe migração simples para bases antigas que não possuíam name.

### Tempo

- resolução de municípios pelo IBGE;
- Cidade e Cidade/UF;
- ambiguidade;
- INMET;
- períodos manhã/tarde/noite;
- consulta por código IBGE;
- cache em memória da lista de municípios.

### Defesa Civil

- feed oficial CAP;
- parsing XML;
- Actual + Public;
- Alert, Update e Cancel;
- referências;
- expiração;
- filtragem textual por município/UF;
- consulta sob demanda;
- limite de alertas;
- fragmentação;
- modos normal, attention e emergency;
- campos configuráveis.

A consulta é deliberadamente independente entre requisições. O sistema atual não mantém histórico de alertas.

### Desenvolvimento

- simulador local;
- pytest;
- Ruff;
- mypy strict;
- Python >= 3.13.

## O que ainda não existe

### Transporte Meshtastic real

Existem adaptadores concretos para Wi-Fi, Bluetooth e USB, com recepção, envio, seleção por `channel_index`, dispositivo opcional e acompanhamento dos eventos de conexão. Ainda faltam reconexão, descoberta de dispositivo e supervisão operacional.

### Execução de produção

environment=production já seleciona o transporte Meshtastic na CLI. Ainda não é considerado pronto para operação 24/7 por faltar reconexão, supervisão e observabilidade.

### Observabilidade completa

Existe logging pontual, porém falta inicialização central por log_level, correlação, métricas, contadores, diagnóstico de transporte e eventos estruturados.

### Defesa Civil event-driven

A consulta atual é sob demanda. O gateway de referência é contínuo e orientado a eventos.

### Geolocalização por polígono

O MeshBot atual usa areaDesc textual. O gateway de referência usa polígonos CAP e point-in-polygon.

### Estado persistente de alertas

Ainda não há armazenamento de último alerta, assinatura, atualização, cancelamento ou retenção.

### Integração com hardware

Ainda não existe camada Meshtastic real.

## Divergências que exigem correção futura

1. transport aceita wifi/bluetooth/usb e possui adaptadores iniciais reais, mas ainda não há reconexão e supervisão.
2. production já possui runtime inicial, mas ainda não é runtime de produção 24/7.
4. channel_name e channel_index são carregados, mas ainda não controlam rádio.
5. weather_provider é configurável, mas a composição atual instancia diretamente INMET.
6. log_level é validado, mas não há inicialização central de logging.
7. Defesa Civil usa weather_timeout_seconds na composição da CLI; o timeout deve ser próprio.
8. A documentação distingue agora os transportes de produção planejados dos transportes atualmente disponíveis.

## Conclusão

O núcleo não deve ser refeito.

A prioridade é fechar as fronteiras já criadas e transformar declarações futuras em capacidades reais, sem perder a testabilidade atual.
