# partiu

Camada brasileira de planejamento de viagem para o Claude Code. Nao refaz busca de
voo nem de hotel — delega isso ao [trvl](https://github.com/MikkoParkkola/trvl) e
ao [travel-hacking-toolkit](https://github.com/borski/travel-hacking-toolkit) — e
resolve o que nenhum dos dois cobre: **custo em reais e documento para passaporte
brasileiro**.


## Skills

| Skill | O que faz |
|---|---|
| `viagem` | orquestra tudo, na ordem certa: documento antes de preco |
| `cambio-br` | PTAX + IOF + spread por meio de pagamento, em reais |
| `documentos-br` | visto, vacina e seguro para passaporte BR, com prazo |
| `roteiro-orcamento` | roteiro dia a dia que cabe no orcamento |
| `dado-datado` | disciplina de fonte e data para dado que estraga |

## Instalando

Requer **Python 3.9+**. Fora o `pytest` (so para rodar os testes), tudo e
biblioteca padrao — nao ha `requirements.txt` porque nao ha o que instalar.

```bash
git clone https://github.com/rodsgobbo/partiu.git
cd partiu
cp .mcp.json.example .mcp.json     # so se for usar o trvl
```

Abra o Claude Code **nesta pasta** — as skills sao de projeto e carregam daqui.
Depois de clonar, reinicie o Claude Code: skills sao lidas na partida.

Os scripts tambem funcionam sozinhos, sem o Claude:

```bash
python .claude/skills/cambio-br/scripts/cambio.py USD 3000          # 156 moedas
python .claude/skills/documentos-br/scripts/visto.py FR PT JP
python .claude/skills/documentos-br/scripts/prazos.py 2027-01-15 --exige-visto
python .claude/skills/viagem/scripts/consolidar.py viagens/exemplo-lisboa-2027-03.json
python dados/passport-index/atualizar.py      # mostra o que mudou desde a ultima vez
python saude.py                               # o que envelheceu, o que vence
python conferir.py                            # o que o arquivo de viagem contradiz
python -m pytest tests/ -q                    # 122 testes
```

`cambio.py` e `atualizar.py` batem em rede (PTAX do Banco Central e o dataset do
passport-index). Os testes nao.

**Um teste falha de proposito quando os dados envelhecem.**
`test_nenhum_dado_esta_vencido` compara a data de cada arquivo de `dados/` com o
prazo declarado nele. Falhar ali nao e bug de codigo, e o projeto avisando que
`dados/passport-index/FONTE.json` precisa de um `atualizar.py`. E o mesmo criterio
que a skill `dado-datado` aplica: numero sem data nao e dado, e lembranca.

## Suas viagens

`viagens/*.json` e ignorado pelo git, menos os `exemplo-*.json`. A pasta guarda
dado pessoal — destino, datas, orcamento, situacao de passaporte — e nao ha motivo
para isso subir junto com o codigo. O formato esta em
[`viagens/_esquema.md`](viagens/_esquema.md), e
[`viagens/exemplo-lisboa-2027-03.json`](viagens/exemplo-lisboa-2027-03.json) mostra
um arquivo completo.

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

| | Como instalar | Licenca |
|---|---|---|
| trvl | binario do release, apontado pelo `.mcp.json` | PolyForm Noncommercial — **uso pessoal apenas** |
| travel-hacking-toolkit | `/plugin marketplace add borski/travel-hacking-toolkit` | MIT |

As duas sao opcionais: as skills daqui rodam sem elas, so nao buscam preco de voo
e hotel. A licenca do trvl vincula o uso do trvl, nao deste repositorio.

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
