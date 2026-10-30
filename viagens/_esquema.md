# Como preencher o arquivo da sua viagem

Cada viagem e um arquivo em `viagens/`, com nome no formato
`destino-ano-mes.json` (por exemplo, `portugal-2027-05.json`). Tudo o que os
comandos do projeto sabem sobre a viagem vem desse arquivo.

Para comecar, copie [`_modelo.json`](_modelo.json). Para ver um arquivo
completo, abra [`exemplo-lisboa-2027-03.json`](exemplo-lisboa-2027-03.json).

O arquivo e escrito em JSON, um formato de texto com chaves e valores. Tres
cuidados bastam: texto vai entre aspas (`"Lisboa"`), numero vai sem aspas (`2`),
e datas seguem sempre o formato ano-mes-dia (`"2027-05-10"`).

Este guia vai do mais importante ao mais especifico. Os campos marcados como
**obrigatorio** precisam estar la; os outros voce acrescenta quando fizer
sentido.

## 1. Os dados gerais da viagem

| Campo | O que colocar | Exemplo |
|---|---|---|
| `destino.cidade` | a cidade, so para voce ler | `"Lisboa"` |
| `destino.pais` | a sigla de duas letras do pais | `"PT"` |
| `datas.ida` e `datas.volta` | os dias de ida e de volta | `"2027-03-10"` |
| `viajantes` | quantas pessoas vao | `2` |
| `moeda_local` | a sigla da moeda do pais | `"EUR"` |
| `meio_pagamento` | como voce vai pagar la fora: `"cartao_credito"`, `"moeda_especie"` ou `"conta_global"` | `"cartao_credito"` |
| `spread` | a taxa do **seu** banco, em decimal (4% e `0.04`). Deixe `null` para usar um valor padrao, que e um chute | `0.04` |

## 2. Os custos: tudo que custa dinheiro

Todo gasto da viagem fica numa lista chamada `custos`. Cada item da lista e uma
linha do total. **Se um valor nao esta aqui, ele nao entra na conta** - nenhum
comando procura dinheiro em outro lugar do arquivo.

Uma linha de custo, no minimo:

```json
{"item": "Passagem ida e volta", "valor": 4200, "moeda": "BRL",
 "por_pessoa": true, "consultado_em": "2026-08-28"}
```

| Campo | O que e |
|---|---|
| `item` | o nome do gasto. **Obrigatorio** |
| `valor` | quanto custa. **Obrigatorio** - mas pode ser `null`, veja abaixo |
| `moeda` | a moeda em que voce paga: `"BRL"`, `"EUR"`, `"USD"`... **Obrigatorio** |
| `por_pessoa` | `true` se o valor e de cada pessoa (e sera multiplicado por `viajantes`); `false` se ja e o valor do grupo. **Obrigatorio** |
| `consultado_em` | o dia em que voce viu esse preco. **Obrigatorio** quando ha preco |

Tres regras que evitam os erros mais comuns:

- **Pagou em reais? Use `"moeda": "BRL"`.** Ai nao ha conversao nem imposto de
  cambio. E o caso de passagem comprada em reais numa agencia brasileira.
- **Errar `por_pessoa` e o erro mais caro do arquivo.** Ele dobra o total, ou
  corta pela metade, e o numero continua parecendo normal.
- **Ainda nao sabe o preco? Use `"valor": null`.** Isso quer dizer "este gasto
  existe, mas ainda nao tem preco" - nao quer dizer zero. A linha aparece numa
  parte separada do relatorio e o total passa a se chamar **PARCIAL**, porque esta
  faltando coisa. Junto, escreva `estimativa` (a faixa que voce imagina, em texto)
  e `quando_cotar` (quando da para saber o preco).

Uma lista de custos vazia e tratada como erro: um total de R$ 0,00 pareceria uma
resposta.

### Campos opcionais da linha de custo

| Campo | Para que serve |
|---|---|
| `volatilidade` | quanto tempo o preco vale: `"alta"` (21 dias, como passagem), `"media"` (60) ou `"baixa"` (180). Sem ele, o projeto assume `"alta"` e avisa |
| `depende_da_janela_aerea` | `true` na linha da passagem. Faz o projeto calcular quando a passagem comeca a ser vendida (veja a secao 6) |
| `noites` | numero de noites, na linha de hospedagem. E conferido contra o roteiro |
| `cidade` | a cidade da hospedagem, quando a viagem passa por varias |
| `taxa_turistica` | na hospedagem: `"inclusa"` se o preco ja traz a taxa da cidade, ou `"separada"` se ela tem linha propria. Sem o campo, o projeto soma uma estimativa e avisa |
| `tendencia` | na passagem: se o preco esta subindo, estavel ou caindo (secao 4) |

### Se a passagem tem escalas

Escala e a parada no meio do caminho para trocar de aviao. Alguns paises pedem
visto **ate para quem so troca de aviao** - os Estados Unidos sao o caso mais
comum. Por isso vale anotar onde estao as escalas:

| Campo | O que colocar |
|---|---|
| `conexoes` | a lista de aeroportos da escala, pela sigla de tres letras: `["LIS"]` |
| `por_conta_propria` | `true` se os voos foram comprados em **bilhetes separados** |
| `margem_conexao` | para bilhete separado: o tempo que voce tem entre os voos, o minimo recomendado para aquele aeroporto e de onde veio esse minimo: `{"minutos": 240, "minima": 180, "fonte": "..."}` |
| `cidade_oculta` | `true` se voce vai descer na escala e nao pegar o ultimo voo do bilhete |
| `bagagem_despachada` | na cidade oculta, `false`, para confirmar que voce vai so com mala de mao |

Por que tanto cuidado:

- **Bilhete separado nao tem protecao.** Se o primeiro voo atrasar e voce perder o
  segundo, o problema e seu. E voce passa pela imigracao do pais da escala para
  despachar a mala de novo, entao vale a regra de **entrada** daquele pais.
- **Na cidade oculta, a mala despachada vai para o destino final do bilhete**, e
  nao para onde voce desce.

O `conferir.py` avisa quando uma escala pede um documento que voce nao anotou ter
(veja `documentos.tem` na secao 3), quando falta a margem do bilhete separado e
quando a cidade oculta nao diz como fica a mala.

## 3. Os documentos

O bloco `documentos` guarda o que a viagem exige e o que voce ja tem.

| Campo | O que colocar |
|---|---|
| `visto` | o que a skill `documentos-br` respondeu, em texto |
| `exige` | a lista do que precisa ser providenciado **antes** da viagem: `"visto"`, `"civp"` (certificado de vacina) e `"eta"` (autorizacao pela internet). `[]` quer dizer "nada a providenciar". Sem o campo, o projeto entende que ainda nao foi verificado |
| `prazos` | quanto tempo cada documento leva **neste destino**, quando voce descobriu no consulado: `{"visto": {"dias": 45, "fonte": "consulado", "consultado_em": "..."}}` |
| `tem` | o que os viajantes ja tem: `["visto:US"]` (visto americano), `["eta:GB"]`, `["eta:CA"]`. Vazio quer dizer "so o passaporte" |

Atencao com a febre amarela: alguns paises pedem a vacina de **quem vem do
Brasil**, mesmo sem pedir visto. Quando for o caso, coloque `"civp"` em `exige`.

## 4. Comprar agora ou esperar

O comando `veredito.py` olha cada passagem e responde **RESERVE**, **ESPERE**,
**MUDE** ou **SEM VEREDITO**, dizendo o que decidiu. Ele usa tres informacoes:

1. **Se o preco ainda vale** - pela data em `consultado_em` e pela `volatilidade`.
2. **Para onde o preco esta indo** - pelo campo `tendencia`.
3. **Ate quando da para decidir** - pelo prazo dos documentos em `exige`.

O prazo do documento sempre manda. Se o preco esta caindo mas o visto precisa
ser pedido logo, a resposta e RESERVE: esperar uma queda que chega depois do prazo
do visto nao e economia. A espera so e indicada quando sobram mais de 14 dias
ate esse prazo.

Se faltar alguma das tres informacoes, a resposta e SEM VEREDITO, com a lista do
que falta.

A `tendencia` vem do historico de precos guardado pelo trvl (`trvl watch history`):

```json
"tendencia": {"direcao": "caindo",
              "faixa": {"min": 3800, "max": 4600, "moeda": "BRL"},
              "fonte": "trvl watch history <id>, 12 pontos",
              "consultado_em": "2026-10-30"}
```

- `direcao` e `"subindo"`, `"estavel"` ou `"caindo"`.
- `faixa` e o preco mais baixo e o mais alto ja vistos. So coloque se tiver de onde
  tirou; sem fonte, deixe de fora.
- A tendencia tambem envelhece: depois de 21 dias, ela precisa ser vista de novo.

Nao use o comando `forecast` do trvl para isso: ele le outro historico, que fica
vazio, e devolve uma resposta neutra que parece real.

## 5. O roteiro, dia a dia

O `roteiro` e a lista de onde voce esta em cada dia. Ha dois tipos de bloco:

| Bloco | Campos | Quando usar |
|---|---|---|
| estadia | `cidade`, `dias`, `noites`, `destaques` | onde voce dorme |
| deslocamento | `trecho`, `dias`, `modo`, `duracao` | onde voce so passa, como um voo ou um trem. **Nao tem `noites`** |

`dias` conta a partir da ida: o dia 1 e o dia da ida. `"2-8"` quer dizer do dia 2
ao dia 8, e `"8"` e so o dia 8. Nao escreva datas no roteiro - o projeto calcula a
partir de `datas.ida`. Guardar a mesma informacao em dois lugares e o jeito mais
facil de um deles ficar errado sem ninguem notar.

`dias` diz **onde** o bloco fica; `noites` diz **quantas** noites voce dorme ali.
Sao informacoes diferentes, por isso as duas existem.

Um deslocamento pode dividir o dia com uma cidade: sair de uma cidade e chegar em
outra no dia 8 e normal. Duas **cidades** no mesmo dia, nao.

## 6. Quando a passagem comeca a ser vendida

As companhias aereas so vendem passagem de **11 a 12 meses antes** do voo. Antes
disso, o site de busca vem vazio - e isso nao quer dizer que nao ha voo, quer
dizer que ainda nao comecou a venda.

Numa ida e volta, quem manda e a **volta**: o bilhete e um so, entao nao adianta a
ida estar a venda se a volta ainda nao esta. Com `depende_da_janela_aerea: true`
na linha da passagem, o `recotar.py` calcula sozinho o dia em que a venda abre.

## 7. As cotacoes guardadas

O bloco `orcamento.cotacoes` guarda quanto vale cada moeda em reais, com a data:

```json
"orcamento": {
  "cotacoes": {"CNY": 0.7579, "USD": 5.38},
  "cotacoes_em": "2026-09-09"
}
```

Ele existe porque o `conferir.py` trabalha sem internet. O total de verdade, com a
cotacao do dia, quem calcula e o `consolidar.py`. Se faltar a cotacao de uma
moeda, o relatorio avisa qual linha ficou de fora, em vez de inventar um valor.

## 8. Datas travadas

Quando voce decide nao fazer algo num dia - por exemplo, nao viajar num feriado -,
anote em `datas_bloqueadas`. Assim o `conferir.py` avisa se o roteiro acabar
marcando algo nesse dia.

| Campo | O que colocar |
|---|---|
| `data` | o dia travado, no formato `"2027-05-01"`. Um item por dia |
| `razao` | o motivo, curto |
| `decisao` | o que voce decidiu por causa disso. **Obrigatorio**: sem ele, daqui a um tempo ninguem lembra por que o dia estava travado |

```json
"datas_bloqueadas": [
  {"data": "2027-05-01", "razao": "Feriado nacional, atracoes lotadas",
   "decisao": "Trem entre as duas cidades movido para o dia seguinte"}
]
```

## 9. O que precisa ser comprado com antecedencia

`itens_com_prazo` lista o que nao da para deixar para a ultima hora, como
ingresso que esgota.

| Campo | O que colocar |
|---|---|
| `item` | o nome |
| `cidade` | a cidade do roteiro onde ele acontece |
| `janela_dias` | so se a venda abre um numero fixo de dias antes da visita (por exemplo, `7`). Se nao ha prazo fixo, deixe sem |
| `critico` | `true` se, sem ele, voce perde a atracao e nao ha plano B |
| `data_compra` | opcional. Se voce anotar, o projeto confere se bate com a data calculada |
| `dias_restritos` | dias da semana em que nao funciona |

Nao use `data_compra` para mandar na data. O projeto calcula a data certa a partir
do roteiro; se o roteiro mudar, a data calculada muda junto, e a anotada a mao
ficaria para tras.

```json
{"item": "Ingresso do museu", "janela_dias": 7,
 "cidade": "Cidade A", "critico": true}
```

## 10. Suas decisoes

`decisoes` e uma lista de frases explicando **por que** voce escolheu o que
escolheu. Nao entra em nenhuma conta. Serve para que, semanas depois, voce (ou o
Claude) nao refaca a mesma pesquisa do zero.

```json
"decisoes": [
  "Marco em vez de julho: a passagem estava bem mais barata fora da alta temporada."
]
```
