# Defesa Civil — estado atual e direção

## Duas funções diferentes

O MeshBot possui hoje consulta sob demanda e pretende futuramente suportar gateway contínuo.

Consulta:

~~~text
usuário -> !defesacivil cidade -> feed -> resposta
~~~

Gateway:

~~~text
feed -> processamento contínuo -> evento -> rádio
~~~

Essas funções não devem ser confundidas.

## Implementação atual

1. resolve município pelo IBGE;
2. baixa CAP;
3. interpreta XML;
4. aceita Actual + Public;
5. processa Alert, Update e Cancel;
6. coleta referências;
7. remove cancelados/superseded presentes na consulta;
8. ignora expirados;
9. compara areaDesc com cidade/UF;
10. limita;
11. fragmenta;
12. responde.

Não há transmissão automática.

## Limitação geográfica

O casamento atual é textual.

Para o gateway contínuo, a direção correta é:

~~~text
latitude/longitude do gateway
          +
polígono CAP
          |
          v
point-in-polygon
~~~

O município presente no texto não deve substituir permanentemente a geometria oficial.

## Referência arquitetural

O projeto de referência defesa-civil-meshtastic-gateway já demonstrou:

~~~text
Feed oficial
    |
CAP/XML
    |
Parser
    |
Status/tipo
    |
Geometria
    |
Localização
    |
Estado
    |
Deduplicação/update/cancel
    |
Conteúdo
    |
Fragmentação
    |
Meshtastic
~~~

O MeshBot deve aproveitar essa experiência, mas respeitar suas próprias portas e domínio.

## Conteúdo oficial

Separar:

- dados oficiais;
- metadados técnicos;
- texto gerado pelo bot.

Texto de Defesa Civil não deve ser resumido por IA ou heurística.

A aplicação pode escolher campos e adicionar estrutura de transporte, mas não alterar o significado.

## Estado futuro

Persistir pelo menos:

- identifier;
- assinatura do conteúdo;
- estado observado;
- sent;
- expires;
- references;
- última ação de transmissão;
- timestamps.

O estado deve sobreviver a reinicializações.

## Deduplicação

A direção correta é identifier + assinatura do conteúdo.

Mesmo identifier + mesma assinatura = duplicado.

Mesmo identifier + assinatura diferente = atualização.

Cancelamento = encerramento.

Expiração = inativo.

## Retenção

O estado deve possuir retenção para não crescer indefinidamente. A referência usa 30 dias.

A política final deve ser configurável e testada.

## Fragmentação

A fragmentação pertence ao transporte. O limite real deve ser respeitado incluindo os marcadores de parte.

## Event-driven

O gateway deve permanecer silencioso em condições normais.

~~~text
sem evento relevante -> sem transmissão
~~~

Esse é um princípio de arquitetura, não apenas uma otimização.
