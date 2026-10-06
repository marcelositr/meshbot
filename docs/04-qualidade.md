# Qualidade, testes e critérios de aceite

## Padrão mínimo

Toda alteração relevante deve passar por:

~~~text
pytest
ruff check .
mypy src
~~~

O projeto usa mypy strict e Ruff com regras de erros, imports, bugs comuns, modernização e simplificação.

## Pirâmide

### Unitários

Devem cobrir domínio, autorização, comandos, configuração, parsing, formatação e políticas.

### Integração

Devem cobrir bot + transporte, autorização + usuários, SQLite, comandos + fakes e fluxos do simulador.

### Hardware

Quando o transporte real existir, testes de hardware ficam separados dos testes determinísticos.

Nenhum teste unitário depende de rádio conectado.

## Rede externa

Testes contra IBGE, INMET e CAP podem existir como ferramentas manuais, mas a suíte automatizada deve usar respostas controladas.

## Casos obrigatórios

Toda nova funcionalidade deve testar:

- caminho normal;
- entrada inválida;
- recurso ausente;
- erro externo;
- limite;
- autorização quando aplicável;
- persistência quando aplicável.

## Defesa Civil

A suíte deve manter cobertura para Alert, Update, Cancel, referências, Actual, Public, expiração, múltiplos info, múltiplos alertas, ausência de alerta, cidade inválida, cidade ambígua, erro do feed e fragmentação.

Para o gateway futuro:

- deduplicação;
- alteração de conteúdo;
- update que deixa a área;
- cancelamento;
- expiração;
- múltiplos polígonos;
- point-in-polygon;
- retenção.

## Usuários e moderação

Cobrir cadastro, duplicidade, nomes Unicode, acentos, espaços, limite, caracteres proibidos, bloqueio, desbloqueio, silenciamento, expiração, admin/admin, persistência e notificações.

## Transporte futuro

Antes de produção:

- conexão;
- envio;
- recepção;
- perda de conexão;
- reconexão;
- mensagem inválida;
- limite;
- shutdown;
- dispositivo ausente.

## Definition of Done

Uma mudança só está pronta quando:

- comportamento implementado;
- dependências isoladas;
- testes existentes;
- erros definidos;
- configuração validada;
- logs suficientes;
- documentação atualizada;
- sem opções mortas;
- simulador sem regressão;
- decisão arquitetural registrada quando necessária.

## Validação final

Antes de uma versão operacional:

1. suíte completa;
2. Ruff;
3. mypy;
4. simulador limpo;
5. cadastro;
6. nome;
7. autorização;
8. moderação;
9. tempo;
10. Defesa Civil;
11. falha externa;
12. banco novo;
13. migração;
14. somente então hardware.
