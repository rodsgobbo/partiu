---
name: cambio-br
description: Calcula quanto uma viagem custa em reais por meio de pagamento - cartao de credito, moeda em especie ou conta global - usando PTAX oficial do Banco Central, IOF e spread. Use sempre que a conversa envolver quanto levar de dinheiro, cartao ou especie, IOF, spread, cambio, "quanto vou gastar em reais", "compensa pagar em real ou em dolar", conta global, ou o custo total de uma viagem internacional. Use tambem quando o usuario comparar formas de pagar no exterior, mesmo sem citar cambio.
---

# Cambio para viajante brasileiro

Nenhuma das ferramentas de viagem existentes faz esta conta. Elas param no preco
da passagem, em moeda estrangeira, sem IOF. A pergunta que o brasileiro faz -
*"quanto isso custa em reais, tudo somado?"* - fica sem resposta.

## Faca a conta com o script, nao de cabeca

```bash
python .claude/skills/cambio-br/scripts/cambio.py USD 3000
python .claude/skills/cambio-br/scripts/cambio.py EUR 1500 --spread-cartao 0.045
```

O script busca a PTAX de venda ao vivo no Banco Central e aplica IOF e spread por
meio de pagamento. Cotacao de cambio e exatamente o tipo de coisa que um modelo
nao deve estimar de memoria: o numero muda todo dia util e o erro e invisivel.

Cobertura: **156 moedas**. O script tenta primeiro a PTAX diaria, que so tem 10
(USD, EUR, GBP, JPY, CHF, CAD, AUD, DKK, NOK, SEK), e cai no boletim de
fechamento do BCB para o resto - peso argentino, lira, baht, peso chileno. O
boletim ja traz a taxa em reais por unidade, entao **nao ha cruzamento nem
estimativa em lugar nenhum**: os dois caminhos sao dado oficial. A saida diz qual
foi usado.

## Spread e do banco, nao do mundo

Os spreads padrao do script sao chute de partida. A diferenca entre 2% e 6% muda
qual meio de pagamento ganha. Pergunte ao usuario o spread do banco dele antes de
recomendar um meio; se ele nao souber, apresente o resultado como faixa, nao como
numero unico.

## O IOF esta verificado, mas nao e estavel

`dados/iof.json` foi fechado em 28/08/2026 contra o Art. 15-B do Decreto
6.306/2007 no Planalto. As seis aliquotas de cambio de pessoa fisica sao **3,5%**
- cartao de credito e debito (VII), saque no exterior (IX), pre-pago e cheque de
viagem (X), especie (XX) e transferencia para o exterior (XXIV).

Duas coisas que importam ao responder:

**Nao use 1,10% para especie.** Era a aliquota do Decreto 8.731/2016, e blog e
casa de cambio ainda repetem, porque o Congresso a restabeleceu por algumas
semanas via Decreto Legislativo 176/2025 antes do STF derrubar. Quem responde
1,10% hoje esta citando uma norma que nao vigora.

**A base juridica e uma liminar.** A decisao que restabeleceu o Decreto
12.499/2025 e cautelar e monocratica (Moraes, 16/07/2025, ADC 96), e o Plenario
do STF ainda vai referenda-la. Se divergir, as aliquotas mudam. O script ja imprime
essa ressalva; nao a omita ao resumir a resposta. `reconferir_em` esta marcado
para 28/11/2026.

**Consequencia pratica:** como o IOF ficou igual nos tres meios de pagamento, o
imposto deixou de ser criterio de escolha. Quem decide agora e o spread - e por
isso perguntar o spread do banco do usuario deixou de ser refinamento e virou a
pergunta principal.

## Como responder

Mostre a PTAX e a data dela, a tabela por meio de pagamento, e qual ganha *para o
perfil daquela viagem* - gasto concentrado em hotel favorece cartao, dinheiro de
rua favorece especie. Termine com o que falta verificar, se faltar.
