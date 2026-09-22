# Esquema de `viagens/<destino>-<ano-mes>.json`

Corrigido em 09/09/2026 pelo primeiro uso real (item 0.4 do backlog), como
estava previsto. O que a viagem da China ensinou esta marcado abaixo.

O formato existe para servir ao `consolidar.py`: cada bloco de custo vira uma
linha do total em reais. Se um campo nao ajuda a consolidar nem a lembrar de uma
decisao, ele nao pertence a este arquivo.

## Regras que valem para todo bloco de custo

**`moeda: "BRL"` significa "ja pago em real", e ai nao ha conversao nem IOF.**
Passagem comprada em reais numa agencia brasileira e o caso comum. Tratar tudo
como moeda estrangeira infla o total com um imposto que nao foi cobrado.

**`por_pessoa`** diz se o valor multiplica por `viajantes`. Errar isso e o erro
mais caro do arquivo, entao ele e obrigatorio em todo bloco de custo.

**`valor: null` significa "conhecido, ainda sem preco"** — nao significa
zero e nao significa inexistente. A linha continua aparecendo, em secao propria, e
o total passa a se chamar PARCIAL. Foi a licao mais cara do primeiro uso real: a
viagem da China guardava o orcamento fora de `custos[]`, o script somou a lista
vazia e imprimiu **TOTAL R$ 0,00 com codigo de saida 0**. Numero errado que sai
calado e pior que erro, e a linha que costuma faltar — a passagem — e justamente
40-60% do orcamento. Hoje `custos` vazio e erro, e linha sem preco e piso
declarado. Mesma decisao que o `prazos.py` tomou para prazo nao apurado.

Com `valor: null`, use `estimativa` (texto, a faixa que voce ainda nao cotou) e
`quando_cotar` (quando da para fechar). Os dois so aparecem na secao de sem preco.

**Todo custo mora em `custos[]`.** Guardar valor em qualquer outro campo cria uma
segunda contabilidade que nenhuma ferramenta le. Na China havia tres: `custos` (vazio),
`orcamento.linhas_brl` (a que se lia) e valores soltos em `upgrades` e
`antes_de_embarcar` — valores que nao entravam em soma nenhuma. Razao e decisao vao
para `decisoes[]`; dinheiro vem para ca.

**`noites`** e opcional e so faz sentido em linha de hospedagem. Quando presente, e
conferido contra a soma das noites do roteiro. Deixar a contagem so no texto do
item (`"Hospedagem, 9 noites"`) nao serve: ler dali seria interpretar prosa, e
prosa que nao se confere e a origem de todos os defeitos que esta conferencia
procura. Sem o campo, a hospedagem simplesmente nao e conferida — e o relatorio diz
isso, em vez de calar.

**`consultado_em`** e obrigatorio em linha com preco. Preco de passagem de tres semanas atras nao e
preco, e lembranca — o `consolidar.py` avisa quando a cotacao envelheceu.

**`volatilidade`** e opcional e diz quanto tempo aquele preco aguenta:
`alta` (21 dias), `media` (60) ou `baixa` (180). Sem o campo, o `recotar.py`
assume `alta` e **diz que assumiu** — nao ha chute calado.

Ela existe porque o prazo unico produzia alarme constante. Tarifa aerea muda toda
semana; uma reserva de imprevisto que voce mesmo arbitrou nao muda nunca. Com os
dois vencendo em 21 dias, a lista de pendencias fica sempre cheia, e lista que
esta sempre vermelha ninguem le — o dia em que a passagem realmente venceu passa
junto. Na viagem da China eram 6 linhas "vencidas" das quais nenhuma era tarifa.

**`depende_da_janela_aerea`** e opcional e booleano. Marca a linha de passagem, e
faz o `recotar.py` trocar a prosa do `quando_cotar` por uma data calculada: a
janela real de venda da companhia, derivada de `datas`. Ver abaixo.

## A janela de venda, e por que ela olha a volta

Companhia poe voo a venda entre ~330 e ~361 dias antes da partida. Antes disso
nao ha o que cotar, e buscador vazio nao significa "nao ha voo" — significa "ainda
nao vendem".

Quem manda e a **ponta mais distante**, nao a mais proxima. Multitrecho e um
bilhete so: nao adianta a ida estar a venda se a volta nao esta. Conferido em
22/09/2026 contra o Kiwi, com controle para separar "fora da janela" de "o backend
falhou":

| Trecho | Distancia | Resultado |
|---|---|---|
| GRU->PEK 10/09/2027 | 353 d | 15 opcoes — dentro |
| PVG->GRU 29/09/2027 | 372 d | 0 opcoes — fora |
| PVG->GRU 01/06/2027 | 252 d | 15 opcoes — controle: a rota existe |

O controle e o que transforma um zero ambiguo em resposta. Sem ele, `count: 0`
tanto pode ser "nao esta a venda" quanto "nao consegui perguntar", e os dois pedem
acoes opostas.

## Campos

| Campo | Tipo | Nota |
|---|---|---|
| `destino.cidade` | texto | so para leitura humana |
| `destino.pais` | ISO-2 | e o que a `documentos-br` consome |
| `datas.ida` / `datas.volta` | AAAA-MM-DD | `ida` alimenta o `prazos.py` |
| `viajantes` | inteiro | multiplicador dos blocos `por_pessoa` |
| `moeda_local` | ISO-3 | moeda do gasto no destino; e nela, e so nela, que a sobretaxa do destino incide |
| `meio_pagamento` | `cartao_credito` \| `moeda_especie` \| `conta_global` | escolhe a linha de IOF e spread |
| `spread` | decimal | o do SEU banco. `null` usa o padrao do script, que e chute |
| `custos[]` | lista | cada item vira uma linha do total |
| `documentos` | objeto | o que a `documentos-br` apurou, com a data |
| `decisoes[]` | lista | por que voce escolheu o que escolheu |
| `roteiro[]` | lista | onde voce esta em cada dia: estadia ou deslocamento |
| `datas_bloqueadas[]` | lista | o recorte conferivel das decisoes que travam uma data |
| `itens_com_prazo[]` | lista | o que precisa ser comprado ou reservado com antecedencia |

`decisoes` nao entra em conta nenhuma. Existe porque planejamento de viagem
acontece em varias conversas ao longo de semanas, e sem registrar o porque, a
sessao seguinte refaz a mesma pesquisa e as vezes chega a outra conclusao.

## `orcamento.cotacoes` — a taxa que a conferencia usa sem rede

Mapa de `moeda` para reais por unidade, com a data em que foi registrada.

```json
"orcamento": {
  "cotacoes": {"CNY": 0.7579, "USD": 5.38},
  "cotacoes_em": "2026-09-09"
}
```

Existe porque a conferencia **nao acessa a rede**: ela precisa falhar por
inconsistencia, nunca por internet fora do ar. O `consolidar.py` busca cotacao ao
vivo e continua sendo quem fecha o total; a conferencia so quer saber se a faixa
que o arquivo declara bate com as linhas que ele tem.

Sem cotacao para uma moeda, a linha fica **de fora da faixa e e nomeada**, e o
relatorio diz quanto do total ficou coberto. Chutar uma taxa ausente produziria uma
faixa com cara de conta fechada, que e o defeito que originou esta conferencia.

`cotacoes_em` importa: taxa de tres semanas atras nao e taxa, e lembranca.

## `roteiro[]` — onde voce esta em cada dia

Duas formas de bloco, e a diferenca entre elas e o que separa estar de passar:

| Bloco | Campos | Nota |
|---|---|---|
| estadia | `cidade`, `dias`, `noites`, `destaques[]` | onde voce dorme |
| deslocamento | `trecho`, `dias`, `modo`, `duracao` | onde voce so passa; **nao tem `noites`** |

`dias` e o intervalo de dias ordinais contados da ida: dia 1 e a ida, `"2-8"` sao
os dias 2 a 8, `"8"` e so o dia 8. As datas saem dai mais `datas.ida`; nenhuma data
ISO e escrita no roteiro, porque dois campos dizendo a mesma coisa e exatamente o
defeito que a conferencia procura.

**`dias` localiza, `noites` conta.** Nao e redundancia, e divisao de papel — e ela
existe porque nenhuma convencao de intervalo fecha para os quatro blocos da primeira viagem real ao mesmo tempo. Com `fim - inicio + 1`, tres batem e o
quarto da 5 contra as 4 declaradas. Se a contagem saisse de `dias`, o leitor teria
de escolher uma convencao, e a convencao escolhida silenciaria justo a divergencia
que precisa aparecer.

Bloco de deslocamento pode dividir o dia com a cidade vizinha — sair de uma cidade no
dia 8 e chegar na seguinte no dia 8 e o normal de um dia de viagem. Duas **cidades** no
mesmo dia, nao.

## `datas_bloqueadas[]` — a decisao virando dado

Uma decisao que trava uma data continua sendo escrita em `decisoes[]`, em prosa,
com o porque inteiro. `datas_bloqueadas[]` e o **recorte conferivel** dela: a mesma
informacao, na forma que uma ferramenta consegue comparar com o roteiro.

| Campo | Tipo | Nota |
|---|---|---|
| `data` | AAAA-MM-DD | a data travada, uma entrada por dia |
| `razao` | texto | curto, para caber no relatorio |
| `decisao` | texto | a decisao de `decisoes[]` que travou esta data |

`decisao` e obrigatorio. Bloqueio sem procedencia e indistinguivel de bloqueio
inventado, e daqui a um ano ninguem lembra por que aquele dia estava travado.

Os tres campos existem porque **prosa nao se confere**. Na primeira viagem real,
duas decisoes moveram um trem e um passeio para fugir de um feriado local,
ficaram registradas, e o bloco `roteiro` continuou na data antiga por
duas semanas — nao havia como nada alem de um leitor humano notar. Escrever a data
duas vezes, uma para gente e uma para maquina, e o preco de a segunda existir.

```json
"datas_bloqueadas": [
  {"data": "2027-05-01", "razao": "Feriado nacional, atracoes lotadas",
   "decisao": "Trem entre as duas cidades movido para o dia seguinte"},
  {"data": "2027-05-02", "razao": "Feriado nacional, atracoes lotadas",
   "decisao": "Trem entre as duas cidades movido para o dia seguinte"}
]
```

## `itens_com_prazo[]` — o que nao da para deixar para depois

Item que so pode ser comprado numa janela fixa, contada da data da visita, declara
`janela_dias`. Quem nao tem prazo fixo **nao declara o campo** — e a maioria.

| Campo | Tipo | Nota |
|---|---|---|
| `janela_dias` | inteiro | so quando o prazo e fixo e contado da data da visita |
| `cidade` | texto | a cidade do roteiro onde o item acontece, para achar a data |
| `critico` | booleano | item sem segunda chance: sem ele, nao entra |
| `data_compra` | AAAA-MM-DD | opcional, e conferido contra a data derivada |
| `dias_restritos` | lista | dias da semana em que o item nao funciona |

**Nao fixe `data_compra` a mao esperando que ela mande.** Ela existe para ser
conferida, nao para ser fonte: a data que vale sai da visita menos a janela. Fixar
a mao e o defeito — mudar o roteiro um dia move a visita, e a data fixa fica para
tras calada. Na primeira viagem real ela estava fixada um dia depois da derivada,
num ingresso que so vende nos 7 dias e sem o qual nao se entra.

A opcionalidade nao e frouxidao, e o que os dados mostraram. Dos quatro itens da
primeira viagem real com prazo, so um tem janela fixa: um ingresso de museu,
`"exatamente 7 dias antes"`. Hospedagem e `"a partir de outubro/2026"`, o guia e
`"algumas semanas antes"` — janelas abertas, que nao viram conta. Obrigar
`janela_dias` neles produziria numero inventado, e numero inventado num campo de
prazo e pior que campo vazio.

`critico` separa o que arruina a viagem do que so incomoda. Ingresso de museu que so vende online e so nos 7 dias: sem reserva, nao entra, e nao ha plano B
no dia. Hotel tem sempre outro hotel.

```json
{"item": "Ingresso do museu", "janela_dias": 7,
 "cidade": "Cidade A", "critico": true}
```
