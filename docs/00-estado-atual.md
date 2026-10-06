# Estado atual

## Resumo

O MeshBot deixou de ser apenas um protótipo de simulador. O código atual já possui um transporte Meshtastic real para USB, Wi-Fi e Bluetooth, reconexão, runtime de produção, serviços externos de tempo e Defesa Civil, persistência de usuários e de alertas, trabalhadores automáticos e uma TUI de simulador.

O que ainda não pode ser declarado concluído é a **validação física com hardware Meshtastic** e alguns refinamentos operacionais.

## Núcleo de mensagens

O domínio possui somente os objetos necessários para transportar mensagens:

- `IncomingMessage(sender_id, text)`;
- `OutgoingMessage(recipient_id, text)`.

A aplicação conversa com transportes por `MessageTransport`, que expõe apenas `receive()` e `send()`.

## Usuários

O cadastro é persistido em SQLite.

Regras atuais:

- node ID no formato `! + 8 caracteres hexadecimais`;
- normalização do node ID para minúsculas;
- nome padrão `Sem nome`;
- nome máximo de 24 caracteres;
- normalização Unicode NFC;
- espaços duplicados são reduzidos;
- letras Unicode, incluindo acentos, são aceitas;
- dígitos são aceitos;
- caixa original é preservada;
- pontuação, símbolos e emojis são rejeitados;
- papéis `user` e `admin`.

Comandos básicos:

- `!registrar`;
- `!nome <nome>`.

## Autorização

Mensagens passam por `AuthorizationPolicy` quando a política é instalada no bot.

- usuário inexistente: rejeitado, exceto `!registrar`;
- usuário bloqueado: rejeitado;
- usuário silenciado: rejeitado;
- usuário autorizado: segue para o `CommandHandler`.

Para um usuário não cadastrado, o bot envia uma instrução curta para usar `!registrar`.

## Moderação

Administradores podem:

- `!bloquear <node_id>`;
- `!desbloquear <node_id>`;
- `!silenciar <node_id> [minutos]`.

Um administrador não pode moderar outro administrador.

As ações geram notificações diretas ao alvo e aos administradores cadastrados.

## Comandos opcionais

A configuração controla cinco capacidades opcionais:

- `ping` → `!ping`;
- `weather_command` → `!tempo <cidade>`;
- `weather_bulletin` → boletim automático;
- `defense_civil_command` → `!defesacivil <cidade>`;
- `defense_civil_monitor` → monitoramento automático.

Sem a tabela `[features]`, todas essas opções assumem `true`, preservando compatibilidade com configurações antigas.

Os comandos básicos de cadastro, nome e moderação não possuem toggle e são sempre compostos.

## Tempo

O serviço atual é INMET e a resolução de municípios usa a API do IBGE.

A consulta aceita:

- nome da cidade;
- `Cidade/UF`;
- código no formato `ibge <código>`.

A resolução ignora diferenças de caixa e acentuação. Cidade ambígua exige UF.

O serviço mantém em memória a lista de municípios do IBGE depois da primeira consulta.

A resposta de `!tempo` é composta por quatro mensagens:

1. cidade e resumo;
2. temperatura mínima/máxima;
3. umidade mínima/máxima;
4. vento.

O intervalo entre respostas é aplicado pelo `MeshBot`.

### Limitação de configuração

`weather.provider` é validado, mas a composição atual instancia diretamente `InmetWeatherService`. Portanto, **INMET é o único provider efetivamente implementado**.

## Boletim automático de tempo

Existe `WeatherBulletinWorker`.

Ele:

- usa os horários configurados de manhã, tarde e noite;
- publica no máximo uma vez por janela por dia;
- consulta o serviço de tempo;
- envia para o destino configurado;
- registra falhas sem derrubar o processo.

É ativado somente quando:

- `features.weather_bulletin = true`;
- `weather.automatic_enabled = true`;
- local e destino estão configurados.

## Defesa Civil

A integração lê o feed CAP oficial e:

- aceita alertas `Actual/Public`;
- processa `Alert`, `Update` e `Cancel`;
- resolve município via IBGE;
- ignora alertas expirados;
- remove alertas cancelados ou substituídos na composição do snapshot;
- filtra a consulta por município/UF usando o texto de `areaDesc`;
- expõe headline/evento, severidade e campos opcionais;
- limita a quantidade exibida;
- fragmenta mensagens longas.

Não existe interpretação semântica do texto oficial.

### Consulta sob demanda

`!defesacivil <cidade>` pode responder em três modos:

- `normal`;
- `attention`;
- `emergency`.

O modo define quais campos são mostrados por padrão. Os `show_*` permitem ajuste fino.

### Gateway automático

O projeto já possui:

- `DefenseCivilPoller`;
- estado persistente SQLite;
- sincronização por snapshot;
- eventos `new`, `updated` e `deactivated`;
- deduplicação por estado/identificador;
- retry com backoff;
- formatter compacto;
- filtragem textual de localização;
- transmissão automática para o destino configurado.

O evento `deactivated` não gera transmissão.

### Limitações atuais

Ainda não existem:

- geometria CAP com point-in-polygon;
- localização por GPS;
- outbox transacional de envio;
- política de retenção configurável para alertas;
- confirmação persistente de entrega;
- mecanismo transacional que garanta que um evento persistido será reenviado após uma falha de transmissão.

O timeout da Defesa Civil é independente do timeout do serviço de tempo e ambos são definidos em suas respectivas seções.

## Transporte Meshtastic

`MeshtasticTransport` implementa o contrato de transporte para:

- USB;
- Wi-Fi;
- Bluetooth.

Ele:

- cria a interface apropriada da biblioteca Meshtastic;
- assina eventos de conexão, perda de conexão e texto recebido;
- coloca mensagens recebidas em uma fila em memória;
- envia texto usando `channel_index`;
- informa estado conectado/desconectado;
- fecha a interface no shutdown;
- recria a interface após perda de conexão;
- usa backoff de reconexão limitado.

A validação atual é unitária, com interfaces simuladas. **Ainda falta teste físico com o hardware que será usado na instalação.**

### Limitações conhecidas

- o canal usado pelo transporte é definido explicitamente por `channel_index`; não há um campo de nome de canal sem efeito.
- Não há descoberta automática de hardware.
- Não há health endpoint.
- A fila de entrada do transporte não possui limite explícito.
- A seleção de provider de transporte é simples e fica na composição da CLI.

## Runtime

`ProductionRuntime`:

- inicia workers em threads;
- chama `process_next_message()` continuamente;
- encerra quando o stop event é acionado;
- encerra workers;
- fecha o transporte;
- registra início e fim;
- transforma falha de worker em solicitação de shutdown.

O runtime é reutilizável e não conhece comandos específicos.

## Simulador e TUI

O simulador usa `SimulatorTransport` em memória.

A TUI em curses oferece:

- histórico de chat;
- timestamp;
- cores por tipo;
- entrada no rodapé;
- identificação clara do destino;
- `MeshBot → TODOS` para broadcast;
- `MeshBot → <node>` para destinatário específico;
- processamento do bot fora da thread de desenho.

O atraso configurado entre respostas é preservado porque o processamento ocorre em thread própria e continua usando o atraso interno do `MeshBot`.

A TUI não deve receber novas alterações de UX agora sem uma necessidade concreta.

## Observabilidade

Existe logging centralizado e contadores básicos:

- `received`;
- `processed`;
- `sent`;
- `rejected`;
- `failures`.

O nível é configurável por `log_level`.

Ainda faltam mecanismos externos de health/status e métricas persistentes.

## Qualidade atual

A suíte automatizada cobre unidade e integração, incluindo:

- configuração;
- comandos;
- usuários;
- autorização;
- moderação;
- notificações;
- runtime;
- observabilidade;
- transporte Meshtastic;
- tempo;
- boletim automático;
- Defesa Civil;
- simulador.

O estado conhecido antes desta revisão era de testes, Ruff e mypy passando; a última alteração ainda precisa ser validada localmente pelo usuário.

## Conclusão

O núcleo e as principais integrações já estão implementados. O projeto não precisa de uma reescrita arquitetural.

O próximo marco importante é validar o transporte real com hardware. Depois disso, os refinamentos devem seguir o roadmap abaixo, sem voltar a expandir a TUI ou introduzir abstrações desnecessárias.
