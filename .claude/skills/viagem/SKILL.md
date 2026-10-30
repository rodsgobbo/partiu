---
name: viagem
description: Orquestra o planejamento completo de uma viagem internacional para brasileiro, do preco da passagem ao custo final em reais, juntando as skills locais com o trvl e o travel-hacking-toolkit. Use sempre que alguem quiser planejar uma viagem, perguntar "quanto custa ir para", "me ajuda a planejar", "vale a pena viajar em", ou trouxer destino e datas. Use tambem quando a pergunta tocar mais de um aspecto da viagem ao mesmo tempo - passagem e hospedagem, ou roteiro e orcamento.
---

# Planejar uma viagem, do inicio ao fim

Junta o que ja existe com o que so este projeto tem. Voo, hotel, trem e milhas
vem de fora - nao reimplemente busca aqui. O que e nosso e a camada brasileira: o
custo em reais e o documento para passaporte BR.

## Divisao de trabalho

| Precisa de | Use |
|---|---|
| voo, data mais barata | trvl (`search_dates`, `find_trip_window`) |
| esperar ou comprar | trvl `watch` (historico de preco) + `veredito.py` |
| milhas, pontos, portal de cartao | travel-hacking-toolkit |
| hotel com taxa, avaliacao, cancelamento | trvl (`search_hotels_with_details`, `hotel_reviews`) |
| trem, onibus, transfer do aeroporto | trvl (`search_ground`, `search_airport_transfers`) |
| mala, clima, franquia de bagagem | trvl (`packing-list`, `get_weather`, `get_baggage_rules`) |
| **custo em reais, IOF, meio de pagamento** | [[cambio-br]] |
| **visto, vacina, seguro, prazo** | [[documentos-br]] |
| **roteiro diario dentro do orcamento** | [[roteiro-orcamento]] |

## O que nao usar do trvl

**`check_visa`.** Erra para passaporte brasileiro: responde "visto exigido" para
todo destino, com `success: true`. Confirmado em 28/08/2026 pelos dois caminhos,
CLI e MCP - `BR -> PT` volta `visa-required`. Use sempre a [[documentos-br]].

**Preco de trecho unico nao e metade de ida e volta.** O `search_flights` cota um
trecho por vez. Somar ida + volta cotadas separadamente superestima, as vezes muito:
em 28/08/2026, GRU->PEK saiu por EUR 852 e PVG->GRU pela mesma ferramenta comecou em
EUR 4.146. Tarifa internacional de trecho unico e outro produto, nao a metade de um
bilhete. Para roteiro que entra por uma cidade e sai por outra, o instrumento e o
**multitrecho cotado como tarifa unica** - e a ferramenta nao monta isso. Cote no
site da companhia e diga ao usuario que a soma de trechos e teto, nunca previsao.

**`search_dates` quando o backend cai.** Devolve `success: true, count: 0` — o
mesmo formato de "nao achei nada" — quando na verdade a chamada ao Google Flights
deu timeout. O `search_flights` na mesma rota revela o erro de verdade. Entao
`count: 0` **nao e resposta**: e ambiguo entre "nao ha voo" e "nao consegui
perguntar". Confirme com `search_flights` antes de dizer ao usuario que nao ha
opcao, senao voce transforma uma falha de rede em conselho de viagem.

**O `forecast` nao preve sozinho.** Ele compara o preco com o historico local em
`~/.trvl/deal-history.json` e exige 30 amostras; sem elas devolve confianca 50 e
`InsufficientData: true`, um "neutro" com cara de resposta. E o historico dos
alertas (`trvl watch add` / `watch history`) mora em outro arquivo, `watch.db`,
que o `forecast` nao le - conferido em 30/10/2026, trvl 1.21.6. A tendencia sai
do `watch history`: crie o alerta assim que a janela de venda abrir, porque
historico nao se recupera depois. Pela MCP, `intent: "forecast"` cai na previsao
do **tempo**; use a CLI.

**Os campos `currency`, `country` e `safety` do `destination_info`.** Voltam
vazios (testado em Lisboa, 28/08/2026): `currency.local_currency` e string vazia
e `exchange_rate` e zero. Quem confiar neles mostra "moeda: " e "cotacao: 0" com
cara de dado. O que presta ali e clima, feriados e fuso - e feriado importa mais
do que parece, porque museu fechado muda o roteiro. Para moeda, [[cambio-br]].

## A ordem importa

Documento antes de preco. Descobrir que o destino exige visto com 60 dias de fila
depois de escolher a data desperdica a pesquisa inteira - e e o unico erro da
lista que impede o embarque.

1. **Documento** - [[documentos-br]] no destino. Se tiver prazo longo, isso limita
   as datas possiveis, e as datas mandam no resto.
2. **Passagem** - trvl e toolkit. Traga o preco na moeda de origem da tarifa, e
   grave os aeroportos de conexao em `conexoes` na linha do voo - o `conferir.py`
   acusa escala que exige visto que a viagem nao tem. Bilhete separado ou cidade
   oculta: marque `por_conta_propria`, porque ai se passa pela imigracao e a mala
   despachada na cidade oculta vai para o destino final do bilhete.
   **Na resposta, o risco vem antes do preco:** bilhete separado nao tem
   protecao se o primeiro voo atrasar, e cidade oculta so funciona com mala de
   mao. Grave `margem_conexao` (com a minima do aeroporto e a fonte) e, na cidade
   oculta, `bagagem_despachada: false` - o `conferir.py` acusa a falta dos dois.
3. **Hospedagem** - com taxa inclusa, nao preco de vitrine. Ao gravar a linha,
   diga se a taxa turistica do destino esta dentro (`"taxa_turistica": "inclusa"`)
   ou fora; sem isso o `consolidar.py` soma a estimada de `dados/taxa-turistica.json`
   e avisa. Taxa de resort e de limpeza sao da propriedade: pergunte ao anuncio.
4. **Custo em reais** - [[cambio-br]] sobre passagem, hotel e gasto estimado.
5. **Roteiro** - [[roteiro-orcamento]] com o que sobrou.
6. **Conferir** - `conferir.py` procura contradicao entre roteiro, decisoes
   e orcamento no arquivo de viagem, ANTES de fechar custo.
7. **Veredito da passagem** - `veredito.py` responde RESERVE, ESPERE, MUDE ou SEM
   VEREDITO. Antes, leia o historico do alerta de preco da rota e grave a
   direcao em `tendencia` na linha da passagem, e declare `documentos.exige`.
   Ver abaixo.
8. **Consolidar** - `consolidar.py` fecha o total em reais.
9. **Depois de comprar** - a skill `gardening` do travel-hacking-toolkit reaudita
   reserva ja feita procurando queda de preco, cabine melhor e mudanca de rota. E
   dinheiro de volta em viagem ja paga, entao vale rodar de tempos em tempos ate
   embarcar, nao so uma vez.

Pare depois do passo 1 se aparecer impedimento. Nao vale gastar as buscas dos
outros passos numa viagem que nao acontece.

Para o passo 1, alem do visto, rode o calendario reverso - e ele que diz se a data
pretendida ainda cabe:

```bash
python .claude/skills/documentos-br/scripts/prazos.py <data-da-ida> --exige-visto
```

## Onde cortar

Depois do `consolidar.py`, que ja lista "onde o dinheiro esta", revise **so as tres
maiores linhas**. Para cada uma, a alavanca e a conta:

| Linha | Alavanca | Como medir |
|---|---|---|
| passagem | data, aeroporto, veredito | busca flexivel (+/- dias) na mesma fonte; secao acima; `veredito.py` |
| hospedagem | bairro, tipo, taxa | `roteiro-orcamento` "Onde se hospedar"; `taxa_turistica` |
| gasto em moeda estrangeira | meio de pagamento | `cambio.py <MOEDA> <valor>`: cartao x conta global |

Entregue cada corte **em reais e com a fonte**, e diga quando a alavanca nao rende:
"mudar a data nao corta, a mais barata e a propria data" e resposta, nao falha.
**Sem meta fixa** de 20% - corte que nao existe nao vira numero. E se a revisao
achar que o preco gravado envelheceu e subiu, isso nao e corte: e o total que
estava baixo, e diga antes de qualquer economia. **Mas antes confira se as duas
cotacoes sao das mesmas datas** - num caso real (30/10/2026) a "alta" era uma
cotacao de outro mes comparada com a das datas da viagem.

## Aeroporto alternativo

Voo mais barato para o aeroporto vizinho so e economia depois de pagar o caminho
ate ele. Compare numa tabela, por trecho:

```
                         principal   alternativo
  passagem (todos)       R$ A        R$ B
  terrestre ida e volta  0           R$ T   (trvl search_ground, por pessoa x viajantes)
  -------------------------------------------
  total                  R$ A        R$ B + T
  tempo extra            -           Xh
```

Diga qual compensa **e por quanto**, com o tempo extra ao lado - R$ 200 de
economia por quatro horas de trem e uma escolha, nao uma resposta. Se o aeroporto
vizinho fica em outro pais, ele passa pela [[documentos-br]] antes de qualquer
preco, e a conexao dele vai para `conexoes`. Os dois precos tem de ser da mesma
fonte e do mesmo dia: comparar Kiwi de hoje com Google da semana passada e
comparar ruido.

## Reservar, esperar ou mudar

Nao responda "compro agora?" de cabeca. A tendencia de preco e o insumo que todo
mundo olha, e e o que menos manda: **prazo de documento vence tendencia.** Esperar
uma queda que chega depois do limite do visto nao e economia.

```bash
python veredito.py viagens/<arquivo>.json
```

Ele junta a idade da cotacao, a `tendencia` gravada do `watch history` e o limite do
documento, e diz qual dos tres decidiu. Repasse esse "decidiu" ao usuario: um
RESERVE porque o preco sobe e um RESERVE porque o visto fecha sao conselhos
diferentes.

SEM VEREDITO nao e falha, e a resposta honesta: falta insumo, e a lista diz qual.
Resolva os que faltam e rode de novo, em vez de decidir sem eles. Se a auditoria
de oferta for o pedido ("esse preco e bom?"), a resposta e a posicao na `faixa`
historica com a fonte dela - nunca uma nota inventada.

## Estado da viagem

Grave o que for decidindo em `viagens/<destino>-<ano-mes>.json`. O formato esta
em `viagens/_esquema.md`, com um exemplo preenchido ao lado. Planejamento de
viagem acontece em varias conversas ao longo de semanas; sem estado gravado, cada
sessao recomeca do zero e o usuario repete tudo.

Duas armadilhas que o esquema resolve e que e facil errar de cabeca:

- **`moeda: "BRL"` nao leva IOF.** IOF de cambio incide sobre operacao de cambio,
  e passagem comprada em reais numa agencia daqui nao teve nenhuma. Tratar tudo
  como moeda estrangeira infla o total com imposto que nao foi cobrado.
- **`por_pessoa` e obrigatorio em todo custo.** Errar isso dobra ou divide o
  total pela metade, e o numero continua parecendo plausivel.

Feche com o script, que ja aplica as duas regras:

```bash
python conferir.py viagens/<arquivo>.json    # antes de fechar o total
python .claude/skills/viagem/scripts/consolidar.py viagens/<arquivo>.json
```

O `conferir.py` roda antes porque total certo sobre roteiro errado continua
errado. Ele nao corrige nada: sai com codigo diferente de zero e diz onde os dois
lados discordam. Corrigir e decisao de quem planeja - reescrever o roteiro
apagaria a razao registrada na decisao, que e a parte cara de reconstruir.

Ele tambem avisa quando alguma cotacao passou de 21 dias. Preco de passagem de
tres semanas atras nao e preco, e lembranca. Ver [[dado-datado]].

## Como responder

Um panorama curto primeiro - da para fazer, quanto custa, o que trava - e o
detalhe depois. Deixe explicito o que e preco real buscado agora, o que e
estimativa e o que ainda nao foi verificado.
