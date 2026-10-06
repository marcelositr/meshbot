# Operação e configuração

## Desenvolvimento

O ambiente de desenvolvimento deve usar:

~~~text
environment = development
transport = simulator
~~~

Instalação:

~~~text
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp config/config.example.toml config/config.toml
python3 -m meshbot
~~~

config/config.toml não é versionado.

## Simulador

Entrada:

~~~text
<node_id> <mensagem>
~~~

Exemplos:

~~~text
!12345678 !registrar
!12345678 !nome Marcelo
!12345678 !ping
!12345678 !tempo Ituverava/SP
!12345678 !defesacivil Ituverava/SP
~~~

Desenvolvimento não deve abrir rádio real por acidente.

## Banco

Padrão: data/meshbot.db.

É persistente, local e não versionado.

Alterações de schema devem possuir migração compatível ou estratégia explícita.

## Configurações

Identidade: name, admins.

Runtime: environment, transport, log_level.

Meshtastic: channel_name, channel_index.

Moderação: default_silence_minutes.

Mensagens: command_prefix, message_delay_seconds.

Tempo: weather.provider, weather.timeout_seconds e weather.periods.

Defesa Civil: enabled, mode, max_alerts, max_message_length e show_*.

## Observabilidade

\`log_level\` é aplicado ao processo na inicialização. Os níveis aceitos são \`DEBUG\`, \`INFO\`, \`WARNING\` e \`ERROR\`.

Em operação, os logs registram:
- início e encerramento do runtime;
- conexão, perda de conexão e reconexão do Meshtastic;
- falhas de envio e de reconexão;
- recebimento e envio de mensagens em nível \`DEBUG\`;
- falhas de processamento.

O conteúdo das mensagens não é colocado nos logs operacionais.

O bot mantém contadores básicos em memória (\`received\`, \`processed\`, \`sent\`, \`rejected\`, \`failures\`) para diagnóstico e futura exposição por health/status ou métricas.

## Transporte Meshtastic

Os transportes \`usb\`, \`wifi\` e \`bluetooth\` possuem adaptador inicial.

\`device\` é opcional:
- USB: caminho da porta serial;
- Wi-Fi: endereço do dispositivo;
- Bluetooth: endereço Bluetooth.

O ambiente de produção não deve assumir uma porta, IP ou endereço fixo.

A integração atual recebe e envia mensagens, acompanha os eventos de conexão e tenta reconectar automaticamente com backoff.

## Produção

Antes de declarar produção pronta, devem existir:

- conexão inicial e estado conectado/desconectado;
- recepção;
- envio;
- reconexão automática;
- timeout;
- seleção de canal;
- identificação do dispositivo;
- shutdown limpo;
- logs;
- testes com hardware.

## Operação segura

O sistema deve:

- falhar fechado na autorização;
- não transmitir em desenvolvimento;
- limitar entrada;
- limitar resposta;
- tratar falhas externas;
- não expor traceback pelo rádio;
- registrar diagnóstico;
- evitar loops.

## Serviços externos

IBGE, INMET e CAP podem falhar.

Uma falha externa não deve derrubar o processo inteiro. O rádio recebe uma mensagem curta; o log preserva diagnóstico.

## Gateway Defesa Civil

O estado dos alertas é separado do cadastro de usuários e persistido em SQLite. Cada alerta é identificado pelo `identifier` oficial do CAP e mantém seu conteúdo, referências, expiração e estado ativo/inativo.

A sincronização trabalha sobre um snapshot efetivo: alertas presentes são atualizados e marcados como ativos; alertas anteriormente ativos que desapareceram do snapshot são marcados como inativos. Isso prepara a aplicação para tratar atualização, cancelamento e expiração sem depender do comando `!defesacivil`.

O gateway contínuo ainda precisa conectar essa camada a uma leitura periódica do feed e, posteriormente, à localização e transmissão automática.

## Futuro serviço contínuo

O gateway deverá ter processo supervisionado, reinício, logs, health/status, métricas, backoff e estado persistente.

systemd é uma opção natural no Linux, mas não deve contaminar a lógica da aplicação.
