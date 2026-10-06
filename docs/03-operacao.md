# Operação e configuração

## Instalação de desenvolvimento

Requisitos:

- Python 3.13 ou superior;
- ambiente virtual recomendado;
- dependências de desenvolvimento para testes, Ruff e mypy.

Fluxo:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp config/config.example.toml config/config.toml
python3 -m meshbot
```

O arquivo `config/config.toml` é local e não deve ser versionado.

## Configuração principal

O exemplo de configuração está organizado por seções para uso por pessoas que não precisam conhecer o código.

### Features

```toml
[features]
ping = true
weather_command = true
weather_bulletin = true
defense_civil_command = true
defense_civil_monitor = true
```

Essas cinco opções são opcionais. Cadastro, nomes e moderação continuam sempre disponíveis.

### Transporte

```toml
transport = "simulator"
```

Para desenvolvimento, use o simulador.

Transportes Meshtastic disponíveis:

- `usb`;
- `wifi`;
- `bluetooth`.

### Administradores

```toml
admins = ["!12345678"]
```

Na inicialização, cada node configurado é criado como admin se ainda não existir ou promovido se existir com outro papel.

### Banco

Padrão:

```text
data/meshbot.db
```

O mesmo arquivo guarda usuários e estado dos alertas de Defesa Civil.

### Moderação

`default_silence_minutes` define a duração usada quando o admin não informa um tempo.

### Log

`log_level` aceita:

- `DEBUG`;
- `INFO`;
- `WARNING`;
- `ERROR`.

### Mensagens

`messaging.message_delay_seconds` controla o intervalo entre respostas consecutivas do mesmo processamento.

O valor padrão do exemplo é 5 segundos.

### Tempo

Configura:

- provider;
- timeout;
- início da manhã;
- início da tarde;
- início da noite;
- boletim automático;
- local;
- destinatário.

Hoje o único provider implementado é INMET.

### Defesa Civil

Configura:

- timeout do serviço de Defesa Civil;
- habilitação da consulta;
- modo;
- quantidade máxima de alertas;
- tamanho máximo;
- campos exibidos;
- monitoramento automático;
- localização;
- destino;
- intervalo de polling.

## Simulador

A entrada é:

```text
<node_id> <mensagem>
```

Exemplos:

```text
!12345678 !registrar
!12345678 !nome Marcelo
!12345678 !ping
!12345678 !tempo Ribeirão Preto/SP
!12345678 !defesacivil Ribeirão Preto/SP
```

A TUI aceita:

- Enter;
- backspace;
- setas esquerda/direita;
- Home/End;
- Ctrl+C;
- `exit`.

A TUI não bloqueia a interface durante o atraso entre respostas.

## Produção

Quando o transporte não é `simulator`, a CLI cria `MeshtasticTransport` e `ProductionRuntime`.

Exemplo de configuração:

```toml
transport = "usb"
device = "/dev/ttyUSB0"
channel_index = 0
```

Wi-Fi usa o endereço configurado em `device`; Bluetooth usa o endereço/nome aceito pelo adaptador Meshtastic.

A produção não deve ser declarada operacional apenas porque o processo inicia. É necessário validar o hardware real.

## Serviço systemd

Existe um exemplo em:

```text
deploy/meshbot.service.example
```

Ele executa:

```text
python -m meshbot
```

e reinicia o processo após falha.

O arquivo é um exemplo; caminhos e usuário devem ser ajustados à instalação real.

## Shutdown

O runtime:

1. sinaliza parada;
2. aguarda workers;
3. fecha o transporte;
4. registra o encerramento.

O transporte Meshtastic remove seus callbacks e fecha a interface.

## Serviços externos

IBGE, INMET e CAP são dependências de rede.

Falhas devem:

- ser convertidas em erro controlado;
- gerar resposta curta quando aplicável;
- registrar diagnóstico;
- não derrubar o processo principal.

## Operação segura

Antes de usar rádio real:

- confirmar `transport`;
- confirmar `device`;
- confirmar `channel_index`;
- confirmar destinatários de automações;
- manter features automáticas desligadas durante testes iniciais;
- validar a identificação do node;
- testar primeiro mensagens simples.

