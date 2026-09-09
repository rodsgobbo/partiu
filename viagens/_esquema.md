# Esquema de `viagens/<destino>-<ano-mes>.json`

Provisorio. Nasceu antes da primeira viagem real (item 0.4 do backlog), entao
espera-se que mude no primeiro uso de verdade — corrija aqui e no exemplo quando
isso acontecer, em vez de contornar no codigo que le.

O formato existe para servir ao `consolidar.py`: cada bloco de custo vira uma
linha do total em reais. Se um campo nao ajuda a consolidar nem a lembrar de uma
decisao, ele nao pertence a este arquivo.

## Regras que valem para todo bloco de custo

**`moeda: "BRL"` significa "ja pago em real", e ai nao ha conversao nem IOF.**
Passagem comprada em reais numa agencia brasileira e o caso comum. Tratar tudo
como moeda estrangeira infla o total com um imposto que nao foi cobrado.

**`por_pessoa`** diz se o valor multiplica por `viajantes`. Errar isso e o erro
mais caro do arquivo, entao ele e obrigatorio em todo bloco de custo.

**`consultado_em`** e obrigatorio. Preco de passagem de tres semanas atras nao e
preco, e lembranca — o `consolidar.py` avisa quando a cotacao envelheceu.

## Campos

| Campo | Tipo | Nota |
|---|---|---|
| `destino.cidade` | texto | so para leitura humana |
| `destino.pais` | ISO-2 | e o que a `documentos-br` consome |
| `datas.ida` / `datas.volta` | AAAA-MM-DD | `ida` alimenta o `prazos.py` |
| `viajantes` | inteiro | multiplicador dos blocos `por_pessoa` |
| `moeda_local` | ISO-3 | moeda do gasto no destino |
| `meio_pagamento` | `cartao_credito` \| `moeda_especie` \| `conta_global` | escolhe a linha de IOF e spread |
| `spread` | decimal | o do SEU banco. `null` usa o padrao do script, que e chute |
| `custos[]` | lista | cada item vira uma linha do total |
| `documentos` | objeto | o que a `documentos-br` apurou, com a data |
| `decisoes[]` | lista | por que voce escolheu o que escolheu |

`decisoes` nao entra em conta nenhuma. Existe porque planejamento de viagem
acontece em varias conversas ao longo de semanas, e sem registrar o porque, a
sessao seguinte refaz a mesma pesquisa e as vezes chega a outra conclusao.
