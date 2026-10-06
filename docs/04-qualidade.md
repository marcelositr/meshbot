# Qualidade, testes e critérios de conclusão

## Ferramentas

O projeto usa:

- pytest;
- Ruff;
- mypy strict.

Configuração relevante:

- Python 3.13;
- Ruff target `py313`;
- linha máxima de 100 caracteres;
- regras Ruff `E,F,I,B,UP,SIM`;
- mypy strict.

## Estrutura de testes

A suíte cobre unidade e integração.

Áreas presentes:

- configuração;
- usuários;
- serviço de usuários;
- autorização;
- bot;
- comandos;
- moderação;
- notificações;
- runtime;
- observabilidade;
- tempo/INMET;
- boletim automático;
- Defesa Civil;
- estado de alertas;
- polling;
- delivery/fragmentação;
- gateway automático;
- transporte Meshtastic;
- simulador.

## Testes de infraestrutura

O transporte Meshtastic é testado com interfaces e eventos simulados, sem exigir rádio físico.

Isso permite validar:

- criação de interface;
- recebimento;
- envio;
- conexão;
- perda de conexão;
- reconexão;
- fechamento.

O teste físico continua separado da suíte automatizada.

## Critério de uma mudança

Uma mudança relevante deve, quando aplicável:

1. ter comportamento definido;
2. possuir teste;
3. manter Ruff limpo;
4. manter mypy limpo;
5. alinhar configuração;
6. alinhar logs;
7. alinhar documentação;
8. registrar limitações conhecidas.

## Definition of Done

Uma funcionalidade só deve ser considerada concluída quando:

- código está implementado;
- caminhos de erro estão tratados;
- testes cobrem o comportamento relevante;
- configuração representa o comportamento real;
- logs são suficientes para diagnóstico;
- documentação não promete algo inexistente.

## Validação local

Fluxo recomendado:

```bash
pytest -q
ruff check .
mypy
```

Para a TUI:

```bash
python3 -m meshbot
```

Esse último comando é interativo e permanece em execução até o usuário sair.

## Hardware

O hardware real não deve ser simulado na suíte unitária.

O aceite do transporte Meshtastic precisa incluir teste físico de:

- conexão inicial;
- identificação;
- recepção;
- envio;
- canal;
- perda de conexão;
- reconexão;
- shutdown.

## Regra de estabilidade

Não alterar código somente para aumentar cobertura numérica.

O objetivo é cobrir contratos e falhas relevantes, mantendo o projeto simples.
