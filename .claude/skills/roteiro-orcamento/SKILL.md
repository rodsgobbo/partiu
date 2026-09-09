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

## Como responder

Roteiro dia a dia, subtotal por dia nas duas moedas, total, folga separada, e uma
linha dizendo quanto sobrou ou faltou em relacao ao que o usuario disse ter. Se
faltou, proponha o corte - nao corte sozinho.
