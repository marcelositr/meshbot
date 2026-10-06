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

## Configurações pendentes

registration_requires_admin aparece no exemplo, mas não é usado. Deve ser implementado ou removido.

weather.provider só deve permanecer configurável se houver intenção real de múltiplos provedores.

transport só deve anunciar opções quando houver adaptadores funcionais.

## Produção

Antes de declarar produção pronta, devem existir:

- conexão;
- recepção;
- envio;
- reconexão;
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

## Futuro serviço contínuo

O gateway deverá ter processo supervisionado, reinício, logs, health/status, métricas, backoff e estado persistente.

systemd é uma opção natural no Linux, mas não deve contaminar a lógica da aplicação.
