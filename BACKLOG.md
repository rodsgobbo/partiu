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

### 0.4 · Viagem real: China, 2027, 20 dias, 3 pessoas · M · **EM ANDAMENTO**
Primeiro uso real, e ele ja pagou o projeto inteiro no passo 1.

**Achado critico:** o dataset dizia `CN: 30` (sem visto) e teria mandado a familia
planejar 2027 sem visto. A isencao e **unilateral e temporaria** — vale ate
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

Pendente: tarifas de 2027 nao estao disponiveis (horizonte de venda e backend
instavel), entao o custo consolidado fica para quando a data estiver definida.

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

### 3.1 · Esquema do `viagens/<destino>.json` · M · **FEITO 28/08/2026 (provisorio)**
`viagens/_esquema.md` mais `viagens/exemplo-lisboa-2027-03.json` preenchido. O
esquema nasceu servindo ao `consolidar.py`: campo que nao ajuda a fechar o total
nem a lembrar de uma decisao nao entrou.
**Marcado provisorio de proposito** — foi escrito antes da primeira viagem real
(item 0.4). Espera-se que mude no primeiro uso; a instrucao no proprio arquivo e
corrigir o esquema, nao contornar no codigo que le.

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

## Fora de escopo, de proposito

- **Busca propria de voo ou hotel.** E manutencao eterna de scraper para empatar
  com quem ja faz. Delegado ao trvl e ao toolkit.
- **Skill de mala.** O trvl ja tem `packing-list`, `get_weather` e
  `get_baggage_rules`. Estava no plano ate a verificacao mostrar que era redundante.
- **Publicar como open source.** Decisao tomada: uso pessoal. Muda a licenca do
  trvl de "ok" para "proibido", entao nao e so uma questao de vontade.

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
- `roteiro-orcamento` nao tem script, e so metodo. Pode ser que precise de um para
  a aritmetica do orcamento; so da para saber depois do 0.4.
