# partiu

**Quanto uma viagem internacional custa, em reais, para um brasileiro — e o que
voce precisa para embarcar.**

Sites de viagem mostram o preco da passagem em dolar ou euro e param por ai. O
que sobra e justamente o que decide se a viagem cabe no bolso: o IOF, o spread do
seu banco, se e melhor pagar no cartao ou levar especie, quanto o hotel fica
depois das taxas, e se o destino exige visto com dois meses de fila.

E isso que este projeto faz. Ele **nao busca voo nem hotel** — deixa isso para
quem ja faz bem — e cuida da parte brasileira da conta.

## Isto serve para voce?

**Serve** se voce esta planejando uma viagem internacional, quer o custo total em
reais sem surpresa, e nao se incomoda de rodar alguns comandos no terminal.

**Nao serve** se voce quer um buscador de passagem. Nao ha um aqui, de proposito.

Voce nao precisa saber programar. Precisa saber abrir um terminal e colar
comandos, e o passo a passo abaixo assume que voce nunca fez isso com este repo.

## O que voce precisa

**Python 3.9 ou mais novo.** So isso. Nao ha `requirements.txt` porque nao ha o
que instalar — tudo usa a biblioteca padrao. (O `pytest` aparece so se voce quiser
rodar os testes.)

Para conferir se voce ja tem:

```bash
python --version
```

O [Claude Code](https://claude.com/claude-code) e **opcional**. Com ele, voce
conversa em portugues e as skills fazem o trabalho. Sem ele, os scripts rodam
sozinhos no terminal, como mostrado abaixo.

## Primeiro uso, em 5 passos

```bash
git clone https://github.com/rodsgobbo/partiu.git
cd partiu
```

**1. Veja quanto custa uma moeda hoje**, com IOF e spread ja aplicados. Comece por
aqui: e o comando que mais rapido mostra para que serve o projeto.

```bash
python .claude/skills/cambio-br/scripts/cambio.py EUR 3000
```

**2. Descubra o que o destino exige** de um passaporte brasileiro.

```bash
python .claude/skills/documentos-br/scripts/visto.py PT FR JP
```

**3. Veja se a data ainda cabe** — o calendario reverso conta para tras a partir
da ida e diz se ainda da tempo de tirar visto e passaporte.

```bash
python .claude/skills/documentos-br/scripts/prazos.py 2027-05-10 --exige-visto
```

**4. Crie o arquivo da sua viagem.** Copie o modelo em branco e edite:

```bash
cp viagens/_modelo.json viagens/portugal-2027-05.json
```

O [`_modelo.json`](viagens/_modelo.json) ja vem com a estrutura certa e comentarios
explicando cada armadilha. O formato completo, campo a campo, esta em
[`viagens/_esquema.md`](viagens/_esquema.md), e
[`exemplo-lisboa-2027-03.json`](viagens/exemplo-lisboa-2027-03.json) mostra um
arquivo real preenchido.

**5. Confira e feche a conta.** Nesta ordem, sempre:

```bash
python conferir.py viagens/portugal-2027-05.json
python .claude/skills/viagem/scripts/consolidar.py viagens/portugal-2027-05.json
```

O `conferir.py` vem antes porque **total certo sobre roteiro errado continua
errado**. Ele procura contradicao — roteiro que discorda do orcamento, decisao que
nunca virou data, cotacao vencida — e nao corrige nada: diz onde os dois lados
discordam e deixa a escolha com voce. O `consolidar.py` entao fecha o total em
reais.

## Ou peca para uma IA fazer

Se voce prefere nao tocar no terminal, aponte um agente de IA para este
repositorio. O [`AGENTS.md`](AGENTS.md) existe para isso: ele carrega as regras que
fazem a conta dar certo, a ordem das etapas e as armadilhas ja descobertas.

Com o Claude Code, abra a pasta e peca em portugues mesmo:

> "planeja uma viagem para Portugal em maio de 2027, somos 2, orcamento de R$ 25 mil"

As cinco skills em `.claude/skills/` carregam sozinhas e cuidam do resto. Depois
de clonar, **reinicie o Claude Code** — skills sao lidas na partida.

## Comandos

```bash
python .claude/skills/cambio-br/scripts/cambio.py USD 3000          # 156 moedas
python .claude/skills/documentos-br/scripts/visto.py FR PT JP
python .claude/skills/documentos-br/scripts/prazos.py 2027-01-15 --exige-visto
python conferir.py                            # confere TODAS as viagens de uma vez
python .claude/skills/viagem/scripts/consolidar.py viagens/<arquivo>.json
python saude.py                               # o que envelheceu, o que vence
python dados/passport-index/atualizar.py      # o que mudou desde a ultima vez
python -m pytest tests/ -q                    # a suite
```

`cambio.py` e `atualizar.py` batem em rede (PTAX do Banco Central e o dataset do
passport-index). O `conferir.py` e os testes **nao** — a conferencia precisa
falhar por inconsistencia, nunca por internet fora do ar.

**Um teste falha de proposito quando os dados envelhecem.**
`test_nenhum_dado_esta_vencido` compara a data de cada arquivo de `dados/` com o
prazo declarado nele. Falhar ali nao e bug de codigo, e o projeto avisando que
algo precisa de um `atualizar.py`. Nao conserte mexendo no teste. E o mesmo
criterio que a skill `dado-datado` aplica: numero sem data nao e dado, e lembranca.

(O numero de testes cresce com os arquivos de viagem que voce tiver no disco —
varios sao parametrizados por `viagens/*.json`.)

## Skills

| Skill | O que faz |
|---|---|
| `viagem` | orquestra tudo, na ordem certa: documento antes de preco |
| `cambio-br` | PTAX + IOF + spread por meio de pagamento, em reais |
| `documentos-br` | visto, vacina e seguro para passaporte BR, com prazo |
| `roteiro-orcamento` | roteiro dia a dia que cabe no orcamento |
| `dado-datado` | disciplina de fonte e data para dado que estraga |

## Suas viagens sao suas

`viagens/*.json` e ignorado pelo git, menos `exemplo-*.json` e `_modelo.json`. A
pasta guarda dado pessoal — destino, datas, orcamento, situacao de passaporte — e
nao ha motivo para isso subir junto com o codigo. Backups (`*.bak`) tambem ficam
de fora, pelo mesmo motivo.

`roteiro-*.html` e `dados_roteiro.json`, saidas do `ferramentas/gerar.py`, tambem
sao ignorados: sao documento de viagem, nao codigo. `decisoes-*.html` idem — sao
paginas de decisao, com orcamento e prazos de quem viaja dentro.

O formato foi corrigido em 09/09/2026 pela primeira viagem real, como o proprio
esquema previa. A licao mais cara: o orcamento estava fora de `custos[]`, o
`consolidar.py` somou a lista vazia e imprimiu **TOTAL R$ 0,00 com codigo de saida
0**. Hoje `custos` vazio e erro, e linha com `valor: null` significa "conhecida,
ainda sem preco" — ela aparece em secao propria e o total passa a se chamar
PARCIAL. Numero errado que sai calado e pior que erro.

## Dependencias externas

As duas sao **opcionais**: as skills daqui rodam sem elas, so nao buscam preco de
voo e hotel.

| | Como instalar | Licenca |
|---|---|---|
| trvl | binario do release, apontado pelo `.mcp.json` | PolyForm Noncommercial — **uso pessoal apenas** |
| travel-hacking-toolkit | `/plugin marketplace add borski/travel-hacking-toolkit` | MIT |

```bash
cp .mcp.json.example .mcp.json     # so se for usar o trvl
```

Se o binario do trvl nao estiver no PATH, troque `trvl` pelo caminho absoluto da
sua maquina. O `.mcp.json` e ignorado pelo git justamente porque esse caminho e
pessoal.

O comando `/plugin` do toolkit **nao existe em todos os ambientes** — na extensao
do VSCode ele responde `isn't available in this environment`. O `BACKLOG.md`, item
0.1, registra a instalacao manual que funciona, incluindo a armadilha de symlink
no Windows e o `enabledPlugins` do `settings.json`, que e o que de fato liga o
plugin.

A licenca do trvl vincula o uso do trvl, nao este repositorio.

## Estado

Rascunho honesto. O que **nao** esta pronto:

- `dados/vacina.json` e `dados/seguro.json` — vazios. Nao existe dataset publico;
  preenchem sob demanda, por destino, com fonte e data.
- Prazos de visto, passaporte e CIVP nao apurados. Aparecem no calendario como
  desconhecidos, de proposito, em vez de sumir.
- A fonte de visto **congelou**. O `passport-index` nao e atualizado desde
  01/03/2026, e o repositorio canonico da categoria esta ainda mais atrasado —
  nao ha dataset gratuito de visto sendo mantido. A confianca do dado caiu para
  `baixa`: ele serve de triagem para varrer 199 destinos, nunca para decidir uma
  compra. Para um destino especifico, o que vale e o consulado, registrado em
  `dados/visto-ressalvas.json`.
- Spread do banco ainda e o padrao chutado do script. Como o IOF ficou igual nos
  tres meios de pagamento desde 2025, e o spread que decide — entao esse chute e
  hoje a maior fonte de erro do total.
- Nenhuma skill passou por eval.

O [`BACKLOG.md`](BACKLOG.md) tem a ordem pensada para resolver isso.

## Licenca

[MIT](LICENSE).
