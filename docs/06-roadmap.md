# Roadmap e governança

## Visão

O MeshBot deve evoluir de um núcleo testável com simulador para um serviço Meshtastic operacional sem perder simplicidade e testabilidade.

A ordem importa.

## P0 — fundação

### Documentação

**Estado: iniciado.**

Arquitetura, contratos, operação, qualidade e roadmap agora possuem registro técnico.

### Alinhar configuração e realidade

Obrigatório:

- remover opções sem efeito ou implementá-las;
- separar timeout da Defesa Civil;
- definir composição de production;
- definir transport;
- aplicar log_level.

Critério: nenhuma configuração deve prometer capacidade inexistente.

## P1 — transporte Meshtastic

**Estado: implementado; validação de hardware real pendente.**

Criar MeshtasticTransport atrás de MessageTransport.

Responsabilidades:

- conexão;
- recepção;
- envio;
- identificação do remetente;
- canal;
- reconexão;
- erro;
- shutdown.

O restante do sistema não deve saber se o transporte usa USB, Bluetooth ou Wi-Fi.

### Aceite

O mesmo conjunto de comandos usado no simulador deve funcionar com o transporte real sem alteração dos casos de uso.

## P1 — runtime de produção

**Estado: implementado.**

Composição explícita:

~~~text
development -> SimulatorTransport
production  -> MeshtasticTransport
~~~

O runtime de produção não deve depender da CLI de desenvolvimento.

## P1 — observabilidade

**Estado: implementado.**

Implementar:

- logging central;
- nível configurável;
- conexão;
- mensagens;
- falhas externas;
- contadores básicos.

O operador deve saber se o processo está vivo, conectado, recebendo, enviando e falhando.

## P2 — gateway Defesa Civil

**Estado: implementação funcional concluída; refinamentos operacionais futuros.**

Depois do transporte real:

- feed contínuo;
- estado persistente;
- deduplicação;
- update;
- cancel;
- expiração;
- geometria;
- localização;
- fragmentação;
- transmissão automática.

Essa função deve ser separada da consulta !defesacivil.

## P2 — localização

Criar LocationProvider com implementações manual e GPS futura.

Criar componente de geometria CAP.

## P2 — estado de alertas

Criar armazenamento próprio para alertas.

Não usar a tabela users para isso.

## P3 — robustez

**Estado: camada operacional principal implementada; evolução contínua.**

Depois das funções centrais:

- retry com backoff;
- health check;
- watchdog;
- shutdown;
- métricas;
- retenção de logs;
- limites de memória;
- prevenção de loops;
- documentação Linux.

## P3 — segurança

**Estado: controles básicos implementados; endurecimento contínuo.**

Reforçar:

- validação de origem;
- limites;
- rate limiting;
- spam;
- auditoria administrativa;
- política de segredos;
- erros seguros.

## O que não deve entrar cedo

Não priorizar painel web, banco remoto, microserviços, filas externas, Kubernetes ou IA para resumir alertas oficiais.

Primeiro o projeto precisa operar uma rede Meshtastic de forma confiável.

## Regra de liderança

Toda mudança futura deve declarar:

- problema;
- decisão;
- impacto;
- teste;
- risco;
- próximo passo.

Nenhuma feature entra apenas porque seria legal.

## Definition of Done

Uma feature só está concluída quando código, testes, erros, configuração, logs e documentação estiverem alinhados.

## Marcos

### Marco A — núcleo funcional

**Atingido.**

Usuários, autorização, moderação, tempo, Defesa Civil sob demanda e simulador funcionam.

### Marco B — fundação documental

**Iniciado.**

Este conjunto formaliza o estado e as lacunas.

### Marco C — rádio real

**Implementação pronta; validação física pendente.**

O transporte Meshtastic já suporta USB, Wi-Fi e Bluetooth, incluindo recepção, envio, conexão, reconexão e shutdown. Falta validar com o hardware específico da instalação.

### Marco D — gateway Defesa Civil

**Concluído na camada funcional.**

A primeira camada persistente já está definida: alertas possuem armazenamento próprio, atualização por identificador e estado ativo/inativo. O sincronizador recebe um snapshot efetivo do feed e desativa alertas que deixaram de existir nele.

O consumo contínuo, estado persistente, deduplicação, atualização/cancelamento, expiração e transmissão automática já estão implementados. Ainda faltam refinamentos de geometria CAP, fragmentação específica para mensagens longas e uma outbox transacional para garantir recuperação de falhas de envio sem perda de evento.

### Marco E — operação contínua

**Implementação inicial concluída.**

Supervisão de workers, retry com backoff, shutdown limpo, logging e exemplo de serviço systemd estão implementados. A outbox transacional, métricas externas e health endpoint permanecem refinamentos opcionais.

## Regra final

O projeto não deve correr para parecer grande.

Ele deve crescer em camadas, com contratos claros, testes reais e responsabilidade operacional.

A ambição é grande; a implementação deve ser disciplinada.
