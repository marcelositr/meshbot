# Contratos e regras

## Identidade de nó

Um node ID válido é ! seguido de 8 caracteres hexadecimais.

A normalização remove espaços externos e converte o hexadecimal para minúsculas.

## Nome amigável

A entrada de !nome é dado controlado.

Regras atuais:

- NFC;
- espaços externos removidos;
- espaços consecutivos reduzidos;
- máximo de 24 caracteres;
- letras Unicode;
- acentos;
- dígitos;
- caixa preservada;
- pontuação rejeitada;
- símbolos rejeitados;
- emojis rejeitados;
- nomes compostos permitidos.

Exemplos válidos: Ana, Ana Clara, João da Silva, José, MARIA, João2.

Exemplos rejeitados: Marcelo 👍, Ana!, João@, Carlos_Silva.

## Cadastro

O comando é !registrar.

A identidade vem do remetente. O usuário não fornece outro node ID.

Fluxo:

~~~text
node desconhecido
   |
   +-- !registrar -> usuário criado
   |
   +-- outro comando -> instrução para registrar
~~~

## Autorização

1. node inexistente -> rejeitado;
2. !registrar é exceção;
3. bloqueado -> rejeitado silenciosamente;
4. silenciado -> rejeitado silenciosamente;
5. usuário ativo -> permitido;
6. administrador ativo -> permitido.

A autorização ocorre antes da execução de comandos.

## Administração

admins define administradores iniciais.

Na inicialização:

- inexistente -> cria admin;
- usuário comum -> eleva para admin;
- nome e estado de moderação são preservados.

Administradores não podem moderar administradores.

## Moderação

Comandos:

- !bloquear node_id;
- !desbloquear node_id;
- !silenciar node_id [minutos].

Regras:

- somente admin;
- alvo cadastrado;
- admin não pode ser alvo;
- duração positiva;
- duração ausente usa padrão;
- nome e demais propriedades são preservados.

## Tempo

!tempo exige localidade.

O resolver aceita cidade ou cidade/UF, usa IBGE e diferencia ambiguidade, cidade inexistente e falha externa.

## Defesa Civil

!defesacivil cidade é consulta sob demanda.

O processamento considera:

- status Actual;
- scope Public;
- Alert;
- Update;
- Cancel;
- referências;
- expiração;
- município/UF.

O desaparecimento de um alerta numa consulta posterior não deve ser interpretado automaticamente como cancelamento. O feed é dinâmico.

## Transporte

IncomingMessage e OutgoingMessage são contratos internos.

O adaptador futuro traduz:

~~~text
Meshtastic -> IncomingMessage
OutgoingMessage -> Meshtastic
~~~

O núcleo não deve carregar detalhes de USB, Bluetooth ou Wi-Fi.

## Limite de mensagem

A Defesa Civil usa atualmente 180 caracteres por mensagem.

A fragmentação deve respeitar o limite, preferir cortes em palavras e dividir palavras excepcionais. Não pode alterar o significado do conteúdo oficial.

Quando houver rádio real, o limite efetivo deve ser responsabilidade do adaptador/configuração do transporte.

## Contratos que não devem ser quebrados casualmente

- identidade por node_id;
- IncomingMessage e OutgoingMessage;
- autorização antes dos comandos;
- separação serviço/infraestrutura;
- testes sem rede;
- testes sem hardware;
- proteção dos administradores;
- validação de entrada.
