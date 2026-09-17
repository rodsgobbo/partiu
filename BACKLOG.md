# Backlog

Ordem pensada para o projeto ser util cedo. O criterio nao e "o que e mais facil",
e **o que destrava o proximo** — por isso instalar as dependencias vem antes de
qualquer skill nova, e o IOF vem antes de qualquer refinamento de cambio.

Tamanhos: `P` ate 30 min · `M` uma sessao · `G` mais de uma sessao.

---

## Marco 0 — pôr de pé

Sem isso nada roda ponta a ponta, e o resto do backlog e teoria.

### 0.1 · Instalar o travel-hacking-toolkit · P
```
/plugin marketplace add borski/travel-hacking-toolkit
/plugin install travel-hacker@borski
```
Os 5 MCPs gratuitos (Skiplagged, Kiwi, Trivago, Ferryhopper, Airbnb) funcionam sem
chave. **Pronto quando:** `/travel-hacker:getting-started` lista o que esta
configurado.

### 0.2 · Instalar o trvl e validar o `.mcp.json` · P · **FEITO 28/08/2026**
trvl 1.21.4 instalado localmente, com o checksum SHA256 conferido contra o
`checksums.txt` do release antes de extrair. Copie o `.mcp.json.example` para
`.mcp.json` — se o binario nao estiver no PATH, troque `trvl` pelo caminho
absoluto da sua maquina. O `.mcp.json` e ignorado pelo git justamente porque esse
caminho e pessoal.
Handshake MCP responde (protocolo 2025-11-25) e expoe **1 tool** (`travel`, ~1.5 KB
de schema) — a economia de contexto que o projeto promete se confirma.
Falta so: reiniciar o Claude Code nesta pasta para o servidor aparecer conectado.

### 0.3 · Rodar as 5 skills uma vez, a seco · P
So para ver se disparam e se os caminhos relativos dos scripts resolvem quando
quem chama e o Claude, nao o terminal. **Pronto quando:** cada uma foi invocada ao
menos uma vez sem erro de caminho.

### 0.4 · Primeira viagem real de ponta a ponta · M · **EM ANDAMENTO**
O primeiro uso de verdade ja pagou o projeto inteiro no passo 1. O caso que
rodou foi um destino na China, e os achados abaixo saem dele.

**Achado critico:** o dataset dizia `CN: 30` (sem visto) e teria mandado planejar
uma viagem futura sem visto. A isencao e **unilateral e temporaria** — vale ate
**31/12/2026**, confirmado na Embaixada da China no Brasil. O passport-index nao
tem campo de validade, entao politica temporaria aparece com cara de permanente.
Resposta do projeto: `dados/visto-ressalvas.json`, um arquivo de ressalvas por
destino com `valido_ate`, fonte, orgao e historico das prorrogacoes, que o
`visto.py` imprime junto da resposta.

**Segundo achado:** o `reconferir_em` que mais importa estava aninhado
(`por_destino.CN`) e o `saude.py` so olhava o topo. Agora busca em qualquer
profundidade e avisa 45 dias antes de vencer.

**Terceiro:** `search_dates` do trvl devolve `success: true, count: 0` quando o
backend cai — indistinguivel de "nao ha voo". Registrado na skill `viagem`.

Pendente: com a viagem longe, a tarifa ainda nao esta a venda (horizonte de venda
e backend instavel), entao o custo consolidado fica para quando a data estiver
definida.

## Marco 1 — `cambio-br` confiavel

Hoje ele calcula uma linha de tres e avisa que nao confia em si mesmo. Util, mas
incompleto.

### 1.1 · Fechar o IOF na fonte primaria · M · **FEITO 28/08/2026**
Lido o Art. 15-B do Decreto 6.306/2007 no Planalto, camada por camada. As seis
aliquotas de cambio de pessoa fisica sao 3,5% (incisos VII, IX, X, XX e XXIV),
por forca do Decreto 12.499/2025. O conflito 1,10% vs 3,5% da especie estava
resolvido: 1,10% e a redacao antiga, restabelecida brevemente pelo DL 176/2025 e
derrubada pela cautelar do STF em ADC 96 (Moraes, 16/07/2025, efeitos desde
11/06/2025). `dados/iof.json` esta `verificado: true`, com historico e
`status_juridico.estavel: false` — a decisao ainda vai a Plenario, reconferir em
28/11/2026.
**Achado que muda o produto:** como as tres formas de pagar ficaram com o mesmo
IOF, o imposto deixou de diferenciar. O spread virou o unico criterio — o que
promove o item 1.2 de refinamento a principal.

### 1.2 · Spread real do seu banco · P
Os padroes (4% cartao, 3% especie, 1% conta global) sao chute. Levantar o do seu
banco e da sua conta global e virar padrao no script.
**Pronto quando:** os defaults refletem os seus numeros, com comentario dizendo de
onde vieram e quando.

### 1.3 · Moeda fora das 10 da PTAX · M · **FEITO 28/08/2026**
Resolvido melhor do que o item pedia. Em vez de cruzar via dolar, o script cai no
**boletim de fechamento do BCB** (`www4.bcb.gov.br/Download/fechamento/AAAAMMDD.csv`),
que publica **156 moedas** com a taxa de venda ja em reais por unidade. Nao ha
cruzamento nem estimativa: os dois caminhos sao dado oficial, e a saida informa
qual foi usado. Testado com ARS 200.000 (`boletim de fechamento, 2026-08-27`).
O item previa marcar a taxa como "cruzada, nao oficial" — essa ressalva deixou de
ser necessaria.

### 1.4 · Comparar com o extrato de uma compra sua · M
O teste que fecha o ciclo: pegar uma compra internacional real do seu cartao e ver
se o script chega no valor que o banco cobrou. Se errar, o erro esta no spread ou
no IOF, e ai voce descobre qual.
**Pronto quando:** diferenca abaixo de 1% num caso real, ou a causa da diferenca
esta entendida e anotada.

---

## Marco 2 — `documentos-br` completo

Visto ja funciona. Vacina e seguro estao vazios de proposito.

### 2.1 · Preencher vacina e seguro para 3 destinos seus · M
Nao tentar cobrir o mundo — preencher sob demanda, comecando pelos destinos que
voce realmente considera. ANVISA para CIVP, site oficial de saude do destino,
norma do bloco para seguro.
**Pronto quando:** 3 entradas em cada JSON, cada uma com fonte e `consultado_em`.

### 2.2 · Prazo por tipo de documento · M · **FEITO 28/08/2026**
`prazos.py` monta o calendario reverso a partir da data da viagem, com data limite
e folga por item, e marca VENCIDO quando ja passou. Testados os tres ramos: folga
larga, apertado e vencido.
A decisao de projeto que importa: item **sem prazo apurado aparece no calendario
como desconhecido**, em secao propria, em vez de sumir da lista. Sumir daria a
impressao de calendario completo, e documento esquecido e o unico erro da lista
que impede o embarque.
Um unico prazo esta verificado — febre amarela, 10 dias, por forca do RSI/2005
(fonte ANVISA). Visto, passaporte, CIVP e ETA variam demais para ter numero
generico honesto, entao entraram como `null` com instrucao de onde apurar.

### 2.3 · Alerta de dado velho · P · **FEITO 28/08/2026**
`visto.py` calcula a idade do dado e, acima de 180 dias, imprime um alerta em
bloco **antes** da resposta detalhada — a ordem importa porque dado velho torna a
resposta possivelmente errada, nao apenas incompleta. A dica de atualizar so
aparece quando o alerta nao dispara, para nao repetir.
Os dois ramos foram testados de fato, com a data do dado simulada em jan/2025
(alerta dispara, "DADO COM 19 MESES") e restaurada para mar/2026 (silencioso).

## Marco 3 — orquestracao

### 3.1 · Esquema do `viagens/<destino>.json` · M · **FEITO 28/08/2026, CORRIGIDO 09/09/2026**

`viagens/_esquema.md` mais `viagens/exemplo-lisboa-2027-03.json` preenchido. O
esquema nasceu servindo ao `consolidar.py`: campo que nao ajuda a fechar o total
nem a lembrar de uma decisao nao entrou. Foi **marcado provisorio de proposito**
em 28/08, por ter sido escrito antes da primeira viagem real (item 0.4), com a
instrucao de corrigir o esquema em vez de contornar no codigo que le.

O provisorio cobrou o preco previsto. A primeira viagem real guardava o orcamento
em `orcamento.linhas_brl`; `custos[]`, o unico campo que o `consolidar.py` le,
estava **vazio**. O script somou a lista vazia e imprimiu **TOTAL R$ 0,00, saindo
com codigo 0**. Nao crashou: respondeu. Numero errado que sai calado, no numero
que o usuario mais olha.

Havia **tres** contabilidades no mesmo arquivo: `custos` (vazia), `linhas_brl` (a
que se lia) e valores soltos em `upgrades` e `antes_de_embarcar`, que nenhuma soma
alcancava.

Corrigido no esquema, nao no contorno, como a instrucao mandava:
- `custos` vazio agora e **erro**, nao total zero.
- `valor: null` significa **conhecido, ainda sem preco**: a linha aparece em secao
  propria, com `estimativa` e `quando_cotar`, e o total passa a se chamar
  **PARCIAL**, declarado como piso. Mesma decisao do `prazos.py` para prazo nao
  apurado - somar so o que tem preco faz o orcamento encolher quanto menos voce
  pesquisou, e a linha que costuma faltar e a passagem.
- As linhas foram migradas com o valor em moeda estrangeira **recuperado** a partir
  do convertido, e o fator conferido contra linhas que traziam as duas moedas. Nao
  foi re-estimativa.

A marca de provisorio saiu em 09/09/2026. Suite de 61 para 66, verificada por
mutacao.

### 3.1-a · O que a validacao da primeira viagem real achou · M

Cinco defeitos, levantados em 09/09/2026, todos com a mesma forma - uma contradicao
entre dois blocos do mesmo arquivo:

| # | Achado | Estado em 11/09/2026 |
|---|---|---|
| 1 | a faixa de orcamento escrita a mao deixava a folga de fora | **o `conferir.py` acusa sozinho**, e mostra o estouro sobre o orcamento informado |
| 2 | o roteiro contrariava duas decisoes que tinham movido datas por causa de um feriado | **acusa sozinho**, citando as decisoes |
| 3 | a contagem de noites dependia de uma data de pouso ainda sem voo comprado | **acusa sozinho**; fecha quando a passagem for comprada |
| 4 | a sobretaxa de pagamento do destino, ja registrada em `dados/`, nao chegava ao total | **fechado**: o `consolidar.py` soma a sobretaxa |
| 5 | a data de compra de um ingresso sem segunda chance estava fixada a mao, um dia errada | **o conferidor nao enxerga** enquanto o item nao estiver em `itens_com_prazo[]` |

O item 3.4 constroi o detector. Ele **nao corrige**: corrigir o arquivo de viagem
esta fora de escopo por decisao de desenho, porque uma correcao automatica apagaria
a razao registrada na decisao.

O quinto e o limite honesto do detector: ele confere o que esta em forma
conferivel, e mais nada. A checagem existe e esta testada - foi ela que achou o
erro de um dia -, mas um item escrito em prosa continua dependendo de alguem ler.

### 3.2 · Reaproveitar o `gardening` do toolkit · P · **FEITO 28/08/2026**
Virou o passo 7 da skill `viagem`, com a observacao de rodar periodicamente ate
embarcar, e nao uma vez so.

### 3.3 · Custo total consolidado · M · **FEITO 28/08/2026**
`consolidar.py` le o arquivo de estado e fecha o total em reais. Importa o
`cambio.py` em vez de reimplementar cotacao e IOF — duas contas de cambio no mesmo
projeto divergem no primeiro ajuste.
Duas regras que o script aplica e que sao faceis de errar a mao: linha em BRL nao
leva IOF (nao houve operacao de cambio), e `por_pessoa` multiplica pelo numero de
viajantes. Alerta tambem quando alguma cotacao passou de 21 dias.
Testado com o exemplo de Lisboa: R$ 25.696,81 para dois, com a linha da passagem
em reais corretamente fora do IOF.

### 3.4 · Conferencia de arquivo de viagem · G · **FEITO 11/09/2026**

Os cinco achados do 3.1-a tem a mesma forma, e corrigi-los a mao nao impede o
sexto. Virou mudanca spec-driven, em `.specs/changes/conferencia-de-viagem/`: 8
requisitos, 7 elementos de design, 48 tarefas em 6 fases (6 delas emendas
descobertas na execucao), `sds validate spec` passando. Suite de 66 para 122.

O projeto ja tinha esse controle para `dados/` - o `saude.py` - e nao tinha nada
equivalente para `viagens/`, onde as decisoes caras moram. O `conferir.py` nasce
irmao dele, na raiz, com o mesmo contrato de codigo de saida.

**Contrato de dados antes da ferramenta.** O desenho descobriu que o conferidor
nao podia ser construido contra as formas de entao: as informacoes que os
requisitos tratam como dado so existiam em prosa. Entraram `datas_bloqueadas[]`,
`itens_com_prazo[]` e `orcamento.cotacoes` no esquema, `noites` na linha de
hospedagem, e `pais` com `valor` numerico nos dados de destino. A prosa nao saiu:
`decisoes[]` continua sendo o registro do porque, e o campo novo e o recorte
conferivel dela.

Decisoes faceis de desfazer sem querer:
1. **`valido_ate` mudou de dono.** Estava no nivel da sobretaxa, ambiguo sobre se
   expira a taxa ou a isencao. Agora mora dentro de `isencao`.
2. **Regra duplicada virou ponteiro.** A mesma sobretaxa estava escrita em dois
   lugares do arquivo de destino; ha teste que falha se voltar a aparecer duas vezes.
3. **`janela_dias` e opcional.** A maioria dos itens com prazo tem janela aberta, e
   obrigar o campo produziria numero inventado num campo de prazo.
4. **`dias` localiza, `noites` conta.** Nenhuma convencao de intervalo fechava para
   todos os blocos do roteiro real ao mesmo tempo; escolher uma silenciaria justo
   a divergencia que precisa aparecer.
5. **Sobretaxa so na `moeda_local`**, e nao em toda linha estrangeira: compra feita
   no Brasil em outra moeda nao passa pela carteira digital do destino.
6. **A deteccao de decisao que nao virou dado e heuristica declarada**:
   vocabulario curto e vies para o silencio. Nao ha como ler a intencao de uma frase.

O que a implementacao ensinou:
1. **`roteiro[]` nunca tinha estado no esquema**, e sustenta o calendario inteiro.
2. **O relatorio dizia "nada se contradiz" sem nenhuma checagem registrada.** Hoje
   diz "NADA FOI CONFERIDO" e sai com codigo 1 - verde por falta de checagem e a
   pior falha num hook, porque parece sucesso.
3. **Estimativa de diaria somada como total** deixava a faixa varias vezes menor, e
   calada. Agora `noites` na linha multiplica.
4. **O conferidor tinha uma copia da formula de cambio**, com nome de variavel
   diferente o bastante para o teste de formula unica nao ver. Hoje o teste procura
   o padrao e vigia os dois arquivos.
5. **REQ-4 e REQ-5 colidiam:** com a sobretaxa automatica, a checagem de ausencia
   acusaria para sempre algo ja dentro do total. Estreitada para o caso real.
6. **Um bug meu e uma verificacao ruim minha.** Chamei o texto da isencao de
   `regra`, nome que ja era a aliquota do IOF, e o consolidar quebrava depois da
   tabela em todo destino com prazo de isencao. Eu tinha verificado olhando o
   comeco da saida com `head`, e o traceback vinha depois. Os testes pegaram.
   **Script se verifica pelo fim da saida e pelo codigo de saida, nunca pelo
   comeco.**
7. **A mutacao achou correcoes desprotegidas.** A Fase 5 cruzou os 37 criterios com
   os testes: 16 so tinham verificacao manual. Ganharam teste, e cada regra foi
   quebrada de proposito ate o teste certo cair.

Checkpoint: `conferir.py` sai 1 no arquivo da viagem real e 0 no exemplo de Lisboa;
`saude.py` sai 0; o `consolidar.py` fecha Lisboa sem sobretaxa.

## Marco 4 — qualidade

Depois que a coisa funciona, nao antes.

### 4.1 · Evals das 5 skills com o `skill-creator` · G
Cada skill roda com e sem, compara, e a descricao passa pelo otimizador de
disparo. O risco real aqui e **subdisparo** — a skill existir e nao ser chamada.
**Pronto quando:** cada skill tem `evals/evals.json` e taxa de disparo medida.

### 4.2 · Testes nos scripts · P · **FEITO 28/08/2026**
`tests/test_viagens.py`, 22 testes, rodando em 0,05 s. **Nenhum toca a rede** — a
cotacao entra como parametro, para o teste falhar por bug e nunca por internet
fora do ar.
Exigiu um refactor pequeno: a aritmetica do `consolidar.py` estava presa dentro do
`main()` e virou a funcao pura `linha_em_brl`. O total do exemplo de Lisboa ficou
igual depois da mudanca (R$ 25.696,81), o que serviu de regressao.
Cobre as duas regras caras de errar (BRL sem IOF, `por_pessoa` multiplicando), a
traducao dos codigos de visto, o filtro de prazos, e a integridade dos dados —
inclusive um teste que falha se alguem marcar a liminar do IOF como estavel sem o
STF ter julgado.
**Verificado por mutacao**, porque suite que passa nao prova nada: quebrei o
tratamento de BRL e o flag de estabilidade, e cada uma derrubou exatamente o teste
correspondente.

### 4.3 · Revisao com `code-review-hardening` · M · **FEITO 28/08/2026**
Revisao tipo `feat` nos 5 scripts, linha a linha. **7 achados bloqueantes**, todos
corrigidos e verificados; suite subiu de 22 para 26 testes. Os tres que mais
importaram:

1. **`atualizar.py` envenenava a procedencia.** Sem `gh` ou sem rede, gravava
   `data_do_dado: "desconhecido"` junto com `verificado: true`. Efeito em cadeia:
   `envelhecimento()` nao consegue ler a data, devolve None, e o alerta de dado
   velho do `visto.py` fica calado **para sempre** — enquanto o arquivo se declara
   verificado. Era a falha exata que o projeto existe para evitar, dentro da
   ferramenta que deveria proteger contra ela. Agora preserva a procedencia
   anterior e marca `verificado: false`.
2. **A formula de conversao estava duplicada.** O `consolidar.py` diz no proprio
   docstring que reaproveita o `cambio.py` "porque duas contas de cambio divergem
   no primeiro ajuste" — e tinha a sua propria copia. Canonizada em
   `cambio.em_reais`, com teste que falha se a copia voltar.
3. **`consolidar.py` somava aliquota nao verificada em silencio.** O `cambio.py`
   marcava com `*`; o total saia limpo. Violava a disciplina central do projeto no
   numero que o usuario mais olha.

Tambem: erro de rede que dava diagnostico errado ("confira o simbolo ISO" quando o
problema era conexao), filtro de prazos que dependia de casar substring em prosa,
divisao por zero em `viajantes`, e crash opaco quando a aliquota e null.

**Nota de processo:** dois patches falharam em silencio por escape de `
` em
heredoc. Um so foi pego porque tinha `assert`; o outro porque conferi a saida em
vez de aceitar "sem erro" como sucesso. Vale lembrar disso: neste ambiente,
edicao de arquivo por heredoc precisa de verificacao explicita.

## Extra, fora do backlog original

### `saude.py` · **FEITO 28/08/2026**
`reconferir_em` e `consultado_em` estavam decorativos: nenhum programa os lia. Um
campo de revalidacao que ninguem consulta e comentario, nao controle — e a
diferenca so aparece no dia em que a aliquota mudou e o total continuou saindo
com cara de certo.
`python saude.py` mostra idade e estado de cada dado, se a FONTE la em cima
envelheceu (distinta da idade da nossa copia), se alguma reconferencia venceu, e
se o trvl esta no caminho do `.mcp.json`. Sai com codigo 1 se ha pendencia, entao
serve em hook ou CI.
Ligado na suite como `test_nenhum_dado_esta_vencido`, que e **um despertador, nao
uma invariante**: ele vai quebrar sozinho com o tempo, sem ninguem mexer em
codigo, e quando quebrar a correcao e reconferir na fonte — nunca afrouxar o
teste. Verificado por mutacao: reconferencia vencida e fonte de 970 dias, os dois
alarmes disparam.

### Pagina de decisoes da viagem · **FEITO 09/09/2026**

`decisoes-*.html` na raiz, ignorado pelo git pelo mesmo motivo de `viagens/*.json`:
tem destino, datas, orcamento e o que foi decidido.

As decisoes ordenadas por prazo, com contagem regressiva calculada na hora de abrir
- nao congelada no dia em que foi gerada. Abre por duplo clique, sem servidor, e
grava as escolhas no `localStorage`. Publicada como Artifact, gravaria na propria
pagina; o caminho ja esta escrito.

Nao confundir com `roteiro-*.html`, que e para ler. Esta e para decidir.

## Fora de escopo, de proposito

- **Busca propria de voo ou hotel.** E manutencao eterna de scraper para empatar
  com quem ja faz. Delegado ao trvl e ao toolkit.
- **Skill de mala.** O trvl ja tem `packing-list`, `get_weather` e
  `get_baggage_rules`. Estava no plano ate a verificacao mostrar que era redundante.
- **Empacotar o trvl junto.** O trvl e PolyForm Noncommercial, uso pessoal apenas.
  Ele fica como dependencia opcional, instalada por quem quiser: a licenca dele
  vincula o uso do trvl, nao este repositorio, que e MIT.

---

## Verificado em campo

- **28/08/2026** — a falha de visto do trvl foi confirmada rodando o binario, nao
  so lendo o codigo: `trvl visa --passport BR --destination FR` devolve
  `visa-required`. Idem PT, JP, CN. Com passaporte finlandes o mesmo comando
  devolve `freedom-of-movement`, o que isola a causa no dataset e nao no comando.
  E a justificativa empirica da skill [[documentos-br]].

## Divida conhecida

- ~~Catalogo de skills da pasta raiz vencido~~ — **resolvido 28/08/2026**.
  Regerado com as 5 skills novas deste projeto: 58 catalogadas, verificador em
  dia, nenhuma copia divergente. `catalogo-skills.html` regerado junto.
- ~~Disciplina do `dado-datado` era so prosa~~ — **resolvido 28/08/2026**.
  Os arquivos de dados usavam tres nomes para "quando conferi" (`consultado_em`,
  `baixado_em`, `data_da_coleta`) e um deles nao declarava `verificado`. Enquanto
  foi assim, nenhum teste conseguia cobrar a disciplina de ninguem — e foi por
  isso que o bug de procedencia do `atualizar.py` sobreviveu ate a revisao.
  Normalizado, com 5 testes de conformidade que varrem todo JSON de `dados/`.
  Verificados por mutacao: voltar a usar `data_da_coleta`, ou marcar
  `verificado: false` sem `pendencia`, derruba a suite.
- ~~Alarme de fonte velha nao tinha saida~~ — **resolvido 09/09/2026**.
  O despertador do `saude.py` tocou sozinho, como previsto: a FONTE do
  passport-index passou de 180 dias. A correcao obvia nao funcionou. Rodar o
  `atualizar.py` rebaixou o **mesmo CSV** — o upstream esta em `9c59780` desde
  01/03/2026, tem 4 commits ao todo e nunca foi um feed. Pior: o canonico da
  categoria (`ilyankou/passport-index-dataset`, 313 estrelas) esta parado em
  18/02/2026, **mais velho que o nosso**. Nao ha dataset gratuito de visto sendo
  mantido.

  Isso expos um defeito no alarme, nao no dado. `saude.py` e `visto.py` tratavam
  como um so caso dois problemas de acoes opostas: **copia atrasada** (some
  rodando o atualizar) e **fonte congelada** (nenhuma execucao muda o numero, so
  resta o consulado). O `visto.py` chegava a mandar, em caixa alta, "rode a
  atualizacao antes de confiar na resposta acima" — instrucao comprovadamente
  inutil. Alarme que aponta a acao errada gasta a confianca de que o proximo
  alarme vai precisar, e alarme sem saida e alarme que alguem desliga.

  `FONTE.json` ganhou o bloco `fonte_congelada` com o achado, a data da
  reconferencia e **`reconferir_em`**; `confianca` caiu de `media` para `baixa`.
  O alarme volta sozinho em 09/12/2026 — e volta pelo walker de `reconferir_em`
  que ja existia, sem codigo especial. Nao e anistia: sem a data de volta, dois
  testes derrubam a suite.

  **Bug fechado no caminho:** o `atualizar.py` preservaria o `fonte_congelada`
  mesmo depois de a fonte voltar a andar, calando o alerta para sempre por um
  motivo ja morto — mesma classe de envenenamento de procedencia que a revisao
  de agosto pegou. Agora o bloco sai junto quando o commit muda, com aviso para
  rever a confianca rebaixada.

  Suite de 57 para 61. Verificado por mutacao nas tres regras novas: tirar o
  `reconferir_em`, fazer o degelo esquecer o bloco e calar toda fonte velha
  derrubaram cada um exatamente o seu teste.

- **O dado de visto e triagem, nao resposta.** Consequencia permanente do item
  acima, nao pendencia: enquanto nao existir fonte mantida, `dados/visto-ressalvas.json`
  preenchido a mao e a unica coisa confiavel para um destino especifico. O
  dataset serve para varrer 199 destinos, nunca para decidir uma compra.

- **O trvl nao sobe nesta maquina.** O `.mcp.json` aponta para um binario que
  existe — o `saude.py` confirma "trvl instalado: sim" — mas o servidor falha ao
  conectar com `EUNKNOWN: uv_spawn`. O item 0.2 fechou dizendo que faltava so
  reiniciar o Claude Code nesta pasta; reiniciou, e nao subiu. Isso **bloqueia a
  pendencia 4 da viagem da China**, o alerta de preco por `watch_price`, que
  deveria ser ligado a partir de outubro/2026. Diagnosticar antes de 15/09.

- **`.specs/` entra no repositorio.** Nao esta no `.gitignore`, de proposito: spec e
  artefato de projeto, nao dado pessoal como `viagens/*.json`. Decisao tomada em
  09/09/2026 e registrada aqui para nao ser desfeita por engano.

- **`sds` so aceita LF.** Editar spec com `Path.write_text` no Windows converte o
  arquivo inteiro para CRLF e o validador passa a alegar que *nenhum* requisito tem
  criterios, inclusive os intocados. Passar `newline="
"`. E primo da nota de
  processo do 4.3 sobre heredoc: neste ambiente, edicao por script precisa de
  verificacao explicita do resultado, nao do codigo de saida.

- `roteiro-orcamento` nao tem script, e so metodo. Pode ser que precise de um para
  a aritmetica do orcamento; so da para saber depois do 0.4.
