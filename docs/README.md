# MeshBot — documentação técnica

## Objetivo

Esta pasta documenta o comportamento real do MeshBot, sua arquitetura, configuração, operação, qualidade, Defesa Civil e próximos passos.

A regra desta documentação é simples: **o código atual é a fonte de verdade**. Roadmap e decisões futuras ficam explicitamente marcados como futuros; uma configuração ou uma intenção não é tratada como capacidade implementada.

## Documentos

- `00-estado-atual.md` — inventário do que realmente existe hoje, incluindo limitações conhecidas.
- `01-arquitetura.md` — camadas, contratos, composição e fluxos.
- `02-contratos.md` — mensagens, usuários, autorização, comandos, transporte e regras de configuração.
- `03-operacao.md` — instalação, configuração, simulador e operação real.
- `04-qualidade.md` — testes, lint, tipagem e critérios de conclusão.
- `05-defesa-civil.md` — consulta sob demanda, gateway automático e lacunas restantes.
- `06-roadmap.md` — ordem de evolução do projeto e itens futuros.

## Princípios

1. **Código real vence intenção.**
2. **Integrações externas ficam atrás de fronteiras testáveis.**
3. **O núcleo não depende do hardware Meshtastic.**
4. **Mensagens de rádio devem ser compactas e previsíveis.**
5. **Texto oficial de Defesa Civil não deve ser reinterpretado ou resumido.**
6. **Configuração deve controlar somente capacidades que realmente existem.**
7. **Toda mudança relevante deve trazer código, testes e documentação coerentes.**
8. **O projeto não deve crescer em complexidade antes de operar o básico de forma confiável.**

## Escopo desta revisão

A documentação foi reavaliada contra a árvore atual do projeto no commit `058fc8e4eab82ff1ce27b8abfe1c24babcaa6bc6` e, principalmente, contra a implementação atual de configuração, composição, transporte Meshtastic, runtime, simulador, serviços de tempo, Defesa Civil, persistência e testes.

O arquivo raiz `README.md` não faz parte desta revisão e não foi usado como fonte de conteúdo técnico.

## Estado geral

O projeto já possui:

- núcleo de mensagens e comandos;
- cadastro, nomes, autorização e moderação;
- SQLite para usuários;
- consulta de tempo via IBGE/INMET;
- consulta de Defesa Civil via CAP;
- estado persistente de alertas;
- monitoramento automático de Defesa Civil;
- boletim automático de tempo;
- transporte Meshtastic para USB, Wi-Fi e Bluetooth;
- reconexão automática do transporte;
- runtime de produção;
- simulador com TUI;
- testes automatizados, Ruff e mypy strict.

A principal etapa externa que ainda falta é **validar fisicamente o transporte Meshtastic com hardware real**. Depois disso, o roadmap deve seguir pelos refinamentos operacionais que ainda faltam.

## Regra para manutenção

Quando uma mudança alterar comportamento, configuração, arquitetura, testes ou estado do roadmap, atualizar os documentos afetados no mesmo ciclo.

