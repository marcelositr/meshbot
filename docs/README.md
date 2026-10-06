# MeshBot — Documentação Técnica

## Propósito

O MeshBot é uma aplicação modular para operar serviços sobre redes Meshtastic sem acoplar a lógica de negócio ao transporte de rádio.

O projeto já possui um núcleo funcional para processamento de mensagens, usuários, autorização, moderação, persistência SQLite, previsão do tempo, consulta de Defesa Civil, simulador e testes.

Esta documentação registra o estado real do sistema, seus contratos, suas decisões arquiteturais e o trabalho futuro necessário.

## Documentos

- 00-estado-atual.md — inventário real do sistema e lacunas.
- 01-arquitetura.md — limites entre domínio, aplicação, infraestrutura e interfaces.
- 02-contratos.md — regras de identidade, usuários, autorização, comandos e mensagens.
- 03-operacao.md — configuração e operação.
- 04-qualidade.md — testes, lint, tipagem e critérios de aceite.
- 05-defesa-civil.md — consulta atual e direção do gateway contínuo.
- 06-roadmap.md — prioridades, governança e cobrança futura.

## Princípios de liderança técnica

### Código real vence intenção

README, configuração e documentação devem ser derivados da implementação. Uma opção de configuração não constitui uma funcionalidade.

### Toda integração externa deve ter uma fronteira

O domínio não deve conhecer SQLite, requests, Meshtastic, XML, TOML ou terminal.

### Rede LoRa é recurso escasso

Mensagens devem ser compactas, previsíveis e justificadas. O bot não deve gerar tráfego periódico sem motivo.

### Informação oficial não deve ser reinterpretada

Alertas da Defesa Civil podem ser formatados e transportados, mas não resumidos ou inventados.

### Segurança vem antes de conveniência

Autorização, moderação, identificação e limites de entrada são parte do produto.

### Toda capacidade nasce com teste

Uma funcionalidade só é concluída quando possui comportamento verificável e documentação correspondente.

## Referência

Esta documentação descreve a árvore main no commit c7a61f8f737bffca3a24873c0389db46e964b4e4 e incorpora as decisões consolidadas durante a análise do projeto e do gateway de Defesa Civil de referência.

Alterações arquiteturais futuras devem atualizar a documentação no mesmo ciclo da mudança.
