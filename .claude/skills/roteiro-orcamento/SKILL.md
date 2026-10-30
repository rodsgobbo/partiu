---
name: roteiro-orcamento
description: Monta roteiro dia a dia que cabe num orcamento em reais, misturando atracoes gratuitas e pagas, com custo estimado por dia e folga para imprevisto. Use sempre que a conversa envolver roteiro, itinerario, "o que fazer em", quantos dias, orcamento de viagem, "quanto levar para passeio e comida", ou planejar os dias de uma viagem. Use tambem quando o usuario ja tem voo e hotel e precisa saber se o resto cabe no bolso.
---

# Roteiro que cabe no orcamento

O trvl e o travel-hacking-toolkit planejam a *viagem* - voo, hotel, trecho de
trem. Nenhum dos dois faz o **orcamento diario de passeio e comida**, que e onde
a viagem estoura na pratica.

## Onde buscar cada coisa

Descoberta de lugar vem das ferramentas que ja existem, nao de memoria:

- `nearby_places`, `travel_guide`, `local_events`, `search_restaurants` (trvl)
- `atlas-obscura` e `tripadvisor` (travel-hacking-toolkit)

Sua contribuicao e o que falta: **encaixar isso num numero em reais e distribuir
pelos dias**.

## O metodo

Converta o orcamento para a moeda local logo no inicio, usando [[cambio-br]] -
raciocinar em duas moedas ao mesmo tempo e como o erro entra.

Distribua por dia com esta forma:

```
Dia 3 - quinta
  Manha    Museu X                    EUR 12
  Tarde    Bairro Y a pe              gratis
  Noite    Jantar no mercado Z        EUR 18
  ---------------------------------------------
  Dia                                 EUR 30   (R$ 181)
```

Tres coisas que fazem diferenca e costumam ser esquecidas:

**Guarde 15% do orcamento como folga**, separada, mostrada como linha propria. Nao
distribua a folga nos dias - folga diluida some no primeiro imprevisto.

**Alterne dia caro com dia barato.** Tres museus seguidos estoura o orcamento e
cansa; a alternancia resolve os dois de uma vez.

**Conte o deslocamento.** Transporte urbano e o custo que some do planejamento e
aparece no extrato.

## Onde se hospedar

O bairro onde se dorme muda o deslocamento de **todos** os dias do roteiro, entao
a escolha so faz sentido depois dele, e nunca por lista generica de "melhores
bairros". Faca depois de ter os destaques por dia, e antes de fechar a hospedagem.

Compare **3 bairros** numa tabela so, por cidade de estadia:

Forma, com numeros ilustrativos (nao cotados):

```
Lisboa, 9 noites, 2 pessoas            Baixa      Alfama     Saldanha
  diaria media (taxa inclusa)          EUR 140    EUR 125    EUR 105
  deslocamento/dia, por pessoa         EUR 3      EUR 6      EUR 9
  ---------------------------------------------------------------------
  estadia + deslocamento               EUR 1.314  EUR 1.233  EUR 1.107
  tempo de deslocamento/dia            30 min     50 min     70 min
```

A regra que decide: **diaria e deslocamento entram juntos, multiplicados pelas
mesmas noites.** Bairro mais barato por noite que obriga dois trajetos de metro por
dia pode sair mais caro no total, e o tempo perdido entra na tabela, nao some.

De onde vem cada numero:
- **diaria** - trivago (`trivago-accommodation-radius-search`, centrado no bairro)
  ou trvl `search_hotels`, com taxa inclusa e com a data da consulta.
- **deslocamento** - para cada dia do roteiro, o trajeto do bairro ate os
  destaques daquele dia e de volta. Tarifa do transporte oficial da cidade, com
  fonte e data; trvl `search_ground` para trajeto mais longo. Dia a pe e zero, e
  diga que e a pe.
- **seguranca** - so com fonte oficial e data (governo local, consulado
  brasileiro, estatistica publica). Sem fonte, a linha **nao entra**: impressao de
  forum com cara de dado e pior que linha vazia. Diga que ficou de fora e por que.

**Faca a conta antes de concluir que o bairro importa.** Em cidade de metro barato
o deslocamento empata: em Pequim (30/10/2026), tres bairros em pontas opostas
diferiram R$ 5 na estadia inteira, com metro de CNY 3 a 5 por viagem. Ai quem
decide e a diaria e o tempo, e diga isso em vez de vender um bairro. O
deslocamento pesa onde o transporte e caro ou o roteiro e longe do centro - taxi,
trem suburbano, bate-volta diario.

**Tipo de hospedagem** (hotel, apartamento, albergue) se compara do mesmo jeito,
pelo total e nao pela diaria: diaria x noites, mais taxa de limpeza e taxa turistica
do anuncio, mais a refeicao que cada um obriga a comprar fora. Cafe incluso no hotel
vale zero de refeicao; cozinha no apartamento troca refeicao de restaurante por
mercado. O preco de refeicao vem com fonte (Numbeo serve, com data); o de mercado,
se for estimado, diga que e. Apartamento: trivago com filtro `kitchen` e Airbnb.
**O Airbnb nao atende a China continental** desde 30/07/2022 - busca vazia la e
resposta, nao falha; use o trivago. No Airbnb, olhe o detalhe do preco: quando ele
traz "Taxes" separado, a taxa turistica costuma estar dentro (em Lisboa, R$ 505,98
para 3 pessoas e 7 noites bate com EUR 4 x 7 x 3), e a linha leva
`"taxa_turistica": "inclusa"`; quando nao traz, deixe sem o campo e o
`consolidar.py` soma a estimada.
Em Pequim (30/10/2026) o albergue tinha a menor diaria e nao o menor total: o cafe
fora come a diferenca.

Viagem por varias cidades: uma tabela por cidade de estadia, e o bairro escolhido
vai para o campo `cidade` e para o nome da linha de hospedagem em `custos[]`.

## Como responder

Roteiro dia a dia, subtotal por dia nas duas moedas, total, folga separada, e uma
linha dizendo quanto sobrou ou faltou em relacao ao que o usuario disse ter. Se
faltou, proponha o corte - nao corte sozinho.
