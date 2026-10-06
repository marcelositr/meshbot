# Roadmap e governança

## Visão

O MeshBot deve evoluir de um núcleo testável para um serviço Meshtastic confiável, mantendo simplicidade, contratos claros e testes sem hardware.

A ordem importa.

## Estado de referência

No estado atual:

- núcleo de mensagens: implementado;
- usuários/autorização/moderação: implementados;
- tempo: implementado;
- Defesa Civil sob demanda: implementada;
- boletim automático: implementado;
- gateway automático de Defesa Civil: implementação funcional inicial concluída;
- transporte Meshtastic USB/Wi-Fi/Bluetooth: implementado;
- reconexão: implementada;
- runtime de produção: implementado;
- TUI do simulador: implementada e estabilizada;
- validação física com hardware: pendente.

## P0 — alinhamento da base

### Documentação
**Estado: concluído nesta revisão.**

A documentação deve descrever o código real e separar claramente capacidade existente de trabalho futuro.

### Configuração
**Estado: parcialmente alinhada.**

Os pontos de configuração desta etapa estão concluídos:

- timeout da Defesa Civil separado do timeout de tempo;
- `environment` removido por não ter responsabilidade própria;
- `channel_name` removido por não controlar o rádio;
- `weather.provider` participa da composição e, no momento, INMET é o único provider implementado;
- features e suas dependências permanecem alinhadas.

Critério atendido: nenhuma opção ativa sugere uma capacidade inexistente.

## P1 — validação do rádio real

**Estado: código implementado; validação física pendente.**

Com hardware Meshtastic, validar:

1. USB;
2. Wi-Fi;
3. Bluetooth, se fizer parte da instalação;
4. conexão inicial;
5. identificação;
6. recepção;
7. envio;
8. `channel_index`;
9. perda de conexão;
10. reconexão;
11. shutdown.

### Aceite

O mesmo conjunto de casos de uso usado no simulador deve funcionar sem alteração da lógica de comandos.

Esse é o próximo grande marco do projeto.

## P1 — runtime de produção

**Estado: implementação inicial concluída; validação operacional pendente.**

Já existe:

- `ProductionRuntime`;
- workers;
- shutdown;
- fechamento do transporte;
- reação a falha de worker;
- exemplo systemd.

Depois do hardware, validar comportamento contínuo real.

## P1 — observabilidade

**Estado: base implementada; refinamento pendente.**

Já existe:

- logging central;
- nível configurável;
- eventos de conexão;
- falhas de transporte;
- contadores em memória;
- logs de processamento.

Futuro:

- health/status;
- métricas externas;
- diagnóstico de estado do transporte;
- eventualmente retenção/rotação de logs conforme a instalação.

## P2 — Defesa Civil

**Estado: funcional inicial implementado; refinamentos pendentes.**

Manter:

- feed contínuo;
- estado persistente;
- update;
- cancel;
- deactivated;
- transmissão automática;
- fragmentação segura.

Evoluir para:

- timeout próprio;
- geometria CAP;
- localização;
- retenção;
- outbox transacional;
- confirmação/recuperação de envio.

A consulta `!defesacivil` continua separada do gateway.

## P2 — localização

Criar, somente quando necessário:

- `LocationProvider`;
- implementação manual;
- implementação GPS futura;
- representação explícita de latitude/longitude.

Depois, integrar com geometria CAP.

## P2 — geometria CAP

Substituir ou complementar o filtro textual por:

```text
localização do gateway
        +
polígono CAP
        ↓
point-in-polygon
        ↓
alerta relevante?
```

O município textual pode continuar como fallback, mas não deve ser confundido com precisão geográfica.

## P2 — estado de alertas

A base já existe.

Futuro:

- assinatura/hash do conteúdo;
- timestamps operacionais;
- estado de transmissão;
- retenção;
- outbox;
- recuperação após reinício.

## P3 — robustez

Prioridades futuras:

- health check;
- watchdog;
- métricas;
- retenção de logs;
- limites de memória;
- prevenção de loops;
- recuperação de falhas de envio;
- documentação operacional Linux.

Retry com backoff, shutdown e supervisão básica já existem e não devem ser recriados.

## P3 — segurança

Controles básicos já existem:

- autorização;
- papéis;
- moderação;
- validação de nome;
- limites de resposta;
- tratamento seguro de erros.

Evolução:

- rate limiting;
- proteção contra spam;
- auditoria administrativa;
- política explícita de segredos;
- validação adicional de origem;
- limites operacionais.

## O que não deve entrar cedo

Não priorizar:

- painel web;
- banco remoto;
- microserviços;
- filas externas;
- Kubernetes;
- IA para resumir alertas oficiais;
- nova rodada de polimento visual da TUI sem problema concreto.

Primeiro: rádio real funcionando de forma confiável.

## Regra de decisão

Toda mudança futura deve responder:

1. Qual problema resolve?
2. Qual decisão foi tomada?
3. Qual impacto tem?
4. Como será testada?
5. Qual o risco?
6. Qual é o próximo passo?

Nenhuma feature entra apenas porque parece interessante.

## Definition of Done

Uma mudança só está concluída quando código, testes, erros, configuração, logs e documentação estão alinhados.

## Próxima sequência prática

A ordem recomendada a partir deste documento é:

```text
1. validar localmente a última mudança do simulador;
2. encerrar a fase de TUI;
3. validar a configuração e a composição já alinhadas;
4. preparar/confirmar o hardware Meshtastic;
5. validar conexão e mensagens reais;
6. validar reconexão;
7. validar runtime contínuo;
8. então refinar Defesa Civil/geometria/localização/outbox;
9. depois endurecer operação e segurança.
```

A etapa 1 não exige nova arquitetura. A etapa 4 é a primeira que depende de hardware real.
