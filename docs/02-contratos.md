# Contratos e regras de comportamento

## Mensagens

`IncomingMessage` representa entrada:

- `sender_id`;
- `text`.

`OutgoingMessage` representa saída:

- `recipient_id`;
- `text`.

Ambos são imutáveis.

## Transporte

O contrato mínimo é:

```python
receive() -> IncomingMessage | None
send(message: OutgoingMessage) -> None
```

O transporte não decide autorização, comandos ou formatação de negócio.

## Identidade

Node IDs válidos:

```text
! + 8 caracteres hexadecimais
```

Exemplo:

```text
!12345678
```

A normalização converte o ID para minúsculas.

## Nome do usuário

O nome:

- é obrigatório quando definido;
- tem máximo de 24 caracteres;
- preserva caixa;
- aceita letras Unicode;
- aceita acentos;
- aceita números;
- aceita espaços;
- normaliza Unicode NFC;
- reduz espaços repetidos;
- rejeita pontuação, símbolos e emojis.

Nomes compostos são válidos.

## Autorização

Estados observados:

```text
não cadastrado
bloqueado
silenciado
autorizado
```

Somente `!registrar` atravessa a exceção para usuário ainda não cadastrado.

## Comandos básicos

Sempre disponíveis:

| Comando | Função |
|---|---|
| `!registrar` | cadastra o próprio node |
| `!nome <nome>` | altera o próprio nome |
| `!bloquear <node_id>` | bloqueia usuário, somente admin |
| `!desbloquear <node_id>` | desbloqueia usuário, somente admin |
| `!silenciar <node_id> [minutos]` | silencia usuário, somente admin |

## Comandos opcionais

| Feature | Comando |
|---|---|
| `ping` | `!ping` |
| `weather_command` | `!tempo <cidade>` |
| `defense_civil_command` | `!defesacivil <cidade>` |

Quando a feature não está habilitada, o comando não é registrado no `CommandHandler`.

## Moderação

Regras:

- somente admin pode moderar;
- solicitante precisa estar cadastrado;
- alvo precisa estar cadastrado;
- admin não pode ser moderado;
- duração de silêncio deve ser positiva;
- duração omitida usa `default_silence_minutes`.

## Respostas múltiplas

Um comando pode retornar várias mensagens.

O `MeshBot` envia a primeira imediatamente e aplica `message_delay_seconds` antes de cada resposta posterior.

Isso é importante para rádio: o atraso não deve ser implementado novamente no comando nem na TUI.

## Broadcast

`^all` é o identificador de broadcast usado pela aplicação.

No simulador, a TUI apresenta esse destino como:

```text
MeshBot → TODOS
```

Um node específico aparece como:

```text
MeshBot → !12345678
```

## Configuração de features

Ausência de `[features]` significa todas as cinco features opcionais ligadas.

A configuração explícita pode desligá-las individualmente.

Dependências:

- `weather.automatic_enabled = true` exige `features.weather_bulletin = true`;
- `defesa_civil.automatic_enabled = true` exige `features.defense_civil_monitor = true`;
- monitoramento automático da Defesa Civil também exige `defesa_civil.enabled = true` e uma localização.

## Ambiente e transporte

Transportes válidos:

- `simulator`;
- `wifi`;
- `bluetooth`;
- `usb`.

O ambiente `development` exige `simulator`.

Importante: a composição atual decide simulador ou Meshtastic pelo valor de `transport`, não por `environment`. Portanto, `environment = production` não substitui a configuração do transporte.

## Canal

`channel_index` é usado pelo transporte Meshtastic no envio.

`channel_name` é carregado e documentado, mas não participa atualmente da seleção do canal no adaptador.

## Defesa Civil

O sistema trabalha com o identificador oficial do alerta e mantém o conteúdo CAP estruturado.

A aplicação pode:

- selecionar campos;
- compactar espaços;
- fragmentar por limite;
- escolher destino;
- adicionar cabeçalhos de transporte.

Não deve alterar o significado do texto oficial.

## Estado de alertas

Eventos:

- `new`;
- `updated`;
- `deactivated`.

A mesma identificação com conteúdo diferente gera atualização.

Alertas desaparecidos de um snapshot bem-sucedido são marcados como inativos.

## Erros externos

Falhas de IBGE, INMET ou CAP são convertidas em erros de serviço e, quando chegam ao comando, viram respostas curtas para o usuário.

Detalhes técnicos ficam no log.

