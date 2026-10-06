# Defesa Civil — estado atual e evolução

## Objetivo

O MeshBot possui duas funções distintas:

1. consulta sob demanda por `!defesacivil`;
2. monitoramento automático do feed para transmissão de eventos relevantes.

A segunda não deve alterar a semântica da primeira.

## Fonte

O adaptador atual consulta o feed CAP oficial:

```text
https://idapfile.mdr.gov.br/idap/api/rss/cap
```

A aplicação trabalha com alertas `Actual` e `Public`.

## Parsing atual

O serviço lê:

- identifier;
- sender;
- sent;
- status;
- msgType;
- scope;
- references;
- event;
- severity;
- urgency;
- certainty;
- areaDesc;
- headline;
- description;
- instruction;
- onset;
- expires.

`Alert` e `Update` são considerados.

`Cancel` fornece referências para remover alertas cancelados do snapshot efetivo.

Atualizações também marcam referências anteriores como superseded para a composição do snapshot.

Alertas expirados não entram no resultado ativo.

## Consulta sob demanda

```text
!defesacivil Cidade/UF
        ↓
IBGE
        ↓
CAP
        ↓
alertas ativos
        ↓
filtro textual de areaDesc
        ↓
modo/configuração
        ↓
fragmentação
        ↓
respostas
```

A localização atual é textual: procura-se o município e a UF normalizados dentro de `areaDesc`.

## Modos

### normal

Por padrão:

- severidade.

### attention

Por padrão:

- severidade;
- instrução;
- urgência.

### emergency

Por padrão:

- severidade;
- descrição;
- instrução;
- urgência;
- certeza.

Os campos podem ser ajustados individualmente por `show_*`.

## Regra de conteúdo

O bot não resume, classifica semanticamente nem reescreve o alerta oficial.

Ele apenas:

- seleciona campos;
- normaliza espaços;
- adiciona estrutura de apresentação;
- fragmenta para o limite configurado.

## Estado persistente

A tabela `defense_civil_alerts` guarda:

- identifier;
- conteúdo CAP;
- referências;
- estado ativo;
- `updated_at`.

O repositório é separado da tabela `users`.

## Sincronização

`DefenseCivilStateService` recebe um snapshot efetivo e produz:

- `new`;
- `updated`;
- `deactivated`.

Regras:

- identifier novo/inativo anteriormente → `new`;
- identifier conhecido com conteúdo diferente → `updated`;
- identifier conhecido sem alteração → nenhum evento;
- alerta ativo que desapareceu do snapshot → `deactivated`.

## Poller

`DefenseCivilPoller`:

- consulta em intervalo configurável;
- persiste o snapshot;
- dispara eventos;
- reinicia o intervalo normal após sucesso;
- usa backoff entre 5 e 60 segundos em falhas.

Uma falha do feed não encerra o processo.

## Entrega automática

`DefenseCivilEventDispatcher` envia somente eventos `new` e `updated`.

`deactivated` não gera mensagem.

A entrega usa:

- resolução textual de localização;
- formatter compacto;
- limite de tamanho;
- destino configurado.

## Limitações

### Geometria

Ainda não há leitura dos polígonos CAP para verificar se o gateway está dentro da área do alerta.

A solução atual é textual por município/UF.

### Localização

Ainda não há `LocationProvider` nem GPS.

O local automático é informado manualmente pela configuração.

### Outbox

A transmissão ainda não possui outbox transacional.

Hoje, se o evento for detectado e o envio falhar, não existe uma fila persistente de reenvio associada àquele evento.

### Retenção

Não há política automática de retenção/limpeza das linhas históricas de alertas.

### Expiração persistente

Alertas expirados deixam de entrar no snapshot efetivo, mas não existe um worker separado dedicado a varrer e alterar somente por relógio.

## Próxima evolução correta

Depois da validação do transporte real:

1. separar o timeout específico da Defesa Civil;
2. definir `LocationProvider`;
3. adicionar geometria CAP/point-in-polygon;
4. decidir política de retenção;
5. avaliar outbox transacional;
6. testar transmissão automática com hardware.

Essas mudanças devem preservar a consulta `!defesacivil` e o princípio de não reinterpretar o texto oficial.
