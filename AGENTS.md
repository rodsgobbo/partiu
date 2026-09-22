# AGENTS.md

Instrucoes para qualquer agente de IA que va trabalhar neste repositorio. Se voce
e um humano, o [README.md](README.md) e mais curto e serve melhor.

## O que este repo e

Camada brasileira de planejamento de viagem. Ele **nao busca voo nem hotel** —
isso e delegado a ferramentas externas. O que existe aqui e o que nenhuma delas
cobre: **quanto a viagem custa em reais** (cambio, IOF, spread, meio de pagamento)
e **o que um passaporte brasileiro precisa** para entrar no destino.

Uma viagem vive num arquivo `viagens/<destino>-<ano-mes>.json`. Os scripts leem
esse arquivo; ele e a fonte da verdade, nao a conversa.

## Regras que nao se negociam

Errar qualquer uma produz um numero plausivel e errado, que e pior que um erro
barulhento. Elas estao implementadas em `conferir.py` e `consolidar.py`, entao
violar uma quebra teste.

| Regra | Por que |
|---|---|
| **`por_pessoa` e obrigatorio em todo bloco de `custos[]`** | errar dobra o total ou corta pela metade, e o resultado continua parecendo plausivel |
| **`moeda: "BRL"` nao leva IOF** | passagem paga em real numa agencia daqui nao teve operacao de cambio; cobrar IOF nela infla o total com imposto que ninguem pagou |
| **Todo dinheiro mora em `custos[]`** | valor guardado em outro campo cria uma segunda contabilidade que nenhum script le |
| **`custos` vazio e erro; `valor: null` e "conhecida, sem preco"** | a lista vazia ja imprimiu `TOTAL R$ 0,00` com codigo de saida 0. Linha sem preco aparece em secao propria e o total vira PARCIAL |
| **`consultado_em` e obrigatorio em linha com preco** | cotacao de mais de 21 dias nao e preco, e lembranca — e os scripts avisam |
| **`datas_bloqueadas[].decisao` e obrigatorio** | bloqueio sem procedencia e indistinguivel de bloqueio inventado |
| **`roteiro[]` usa dias ordinais, nunca data ISO** | dois campos dizendo a mesma coisa e exatamente o defeito que a conferencia procura |
| **Nao fixe `itens_com_prazo[].data_compra` a mao** | ela existe para ser conferida contra a data derivada da visita, nao para mandar |

E a regra que governa as outras, da skill `dado-datado`: **numero sem data nao e
dado, e lembranca.** Todo dado que estraga — aliquota, exigencia de visto,
cotacao — carrega a data em que foi apurado e a fonte.

## A ordem importa

Documento **antes** de preco. Descobrir que o destino exige visto com 60 dias de
fila depois de escolher a data joga fora a pesquisa inteira, e e o unico erro da
lista que impede o embarque.

1. **Documento** — skill `documentos-br` no destino. Se houver prazo longo, ele
   limita as datas, e as datas mandam no resto. **Pare aqui se aparecer
   impedimento.**
2. **Passagem** — ferramentas externas. Traga o preco na moeda de origem da tarifa.
3. **Hospedagem** — com taxa inclusa, nao preco de vitrine.
4. **Custo em reais** — skill `cambio-br` sobre passagem, hotel e gasto estimado.
5. **Roteiro** — skill `roteiro-orcamento` com o que sobrou.
6. **Conferir** — `conferir.py`, que procura contradicao **antes** de fechar custo.
7. **Consolidar** — `consolidar.py` fecha o total em reais.

O passo 6 vem antes do 7 de proposito: total certo sobre roteiro errado continua
errado. O `conferir.py` nao corrige nada — ele sai com codigo diferente de zero e
diz onde os dois lados discordam. Corrigir e decisao de quem viaja: reescrever o
roteiro apagaria a razao registrada em `decisoes[]`, que e a parte cara de
reconstruir.

## Comandos

```bash
python conferir.py viagens/<arquivo>.json                     # contradicoes, antes do total
python .claude/skills/viagem/scripts/consolidar.py viagens/<arquivo>.json   # total em reais
python saude.py                                               # o que envelheceu, o que vence
python -m pytest tests/ -q                                    # a suite
python .claude/skills/cambio-br/scripts/cambio.py USD 3000    # 156 moedas
python .claude/skills/documentos-br/scripts/visto.py FR PT JP
python .claude/skills/documentos-br/scripts/prazos.py 2027-01-15 --exige-visto
python dados/passport-index/atualizar.py                      # o que mudou na fonte
```

Python 3.9+, so biblioteca padrao (o `pytest` e so para os testes). `cambio.py` e
`atualizar.py` acessam a rede; `conferir.py` e os testes **nao** — a conferencia
precisa falhar por inconsistencia, nunca por internet fora do ar.

**Um teste falha de proposito quando os dados envelhecem.**
`test_nenhum_dado_esta_vencido` compara a data de cada arquivo de `dados/` com o
prazo declarado nele. Falhar ali nao e bug: e o projeto pedindo uma atualizacao.
Nao "conserte" mexendo no teste.

## Armadilhas confirmadas em campo

Cada uma destas custou uma sessao para descobrir. Nao repita.

- **`check_visa` do trvl erra para passaporte brasileiro.** Responde "visto
  exigido" para todo destino, com `success: true`. Use sempre a `documentos-br`.
- **Preco de trecho unico nao e metade da ida e volta.** Somar ida + volta cotadas
  separadamente superestima, as vezes muito: GRU->PEK saiu EUR 852 e PVG->GRU, na
  mesma ferramenta, comecou em EUR 4.146. Para roteiro que entra por uma cidade e
  sai por outra, o instrumento e o **multitrecho como tarifa unica**, e as
  ferramentas nao montam isso — cote no site da companhia e diga que a soma de
  trechos e teto, nunca previsao.
- **`search_dates` devolve `success: true, count: 0` quando o backend cai** — o
  mesmo formato de "nao achei nada". `count: 0` nao e resposta: confirme com outra
  chamada antes de dizer que nao ha voo, senao voce transforma falha de rede em
  conselho de viagem.
- **Os campos `currency`, `country` e `safety` do `destination_info` voltam
  vazios.** Quem confia neles mostra "moeda: " e "cotacao: 0" com cara de dado.
  Para moeda, `cambio-br`.
- **Agregador tem janela de venda.** Em 22/09/2026 o Skiplagged recusou uma data
  de 10/09/2027: `"Must be no greater than 2027-08-17"`. Viagem a mais de ~11
  meses nao e cotavel, e isso nao e erro de configuracao.
- **Itinerario barato pode ser impossivel.** Buscadores devolvem rotas com
  conexao em Chicago, Toronto ou Vancouver sem saber que brasileiro precisa de
  visto americano (nao existe transito sem visto nos EUA) e de eTA canadense.
  Sempre cheque a nacionalidade das conexoes contra a `documentos-br`.
- **A fonte de visto esta congelada.** O `passport-index` nao e atualizado desde
  01/03/2026 e a confianca do dado e `baixa`: serve de triagem para varrer 199
  destinos, nunca para decidir uma compra. Para um destino especifico vale o
  consulado, registrado em `dados/visto-ressalvas.json`.

## Fora de escopo, de proposito

Nao implemente estas coisas. A ausencia e decisao, nao esquecimento.

- **Busca propria de voo ou hotel.** E manutencao eterna de scraper para empatar
  com quem ja faz.
- **Skill de mala, clima ou franquia de bagagem.** As ferramentas externas ja tem.
- **Empacotar as dependencias externas junto.** Licencas diferentes.

## Onde as coisas moram

| Caminho | O que e |
|---|---|
| `viagens/*.json` | uma viagem por arquivo. **Dado pessoal, ignorado pelo git** |
| `viagens/_esquema.md` | o formato, campo a campo, com o porque de cada regra |
| `viagens/_modelo.json` | esqueleto em branco para copiar |
| `viagens/exemplo-*.json` | exemplo completo e publico |
| `.claude/skills/` | as 5 skills, cada uma com `SKILL.md` e `scripts/` |
| `dados/` | dado que estraga, cada arquivo com fonte e data |
| `ferramentas/` | geradores de HTML e manutencao |
| `conferir.py` `saude.py` | conferencia e validade dos dados |
| `BACKLOG.md` | o que falta, em ordem, e o que ja foi verificado em campo |
| `.specs/` | requisitos e design de mudancas maiores |

## Ao mexer no repo

- **`viagens/*.json` e dado pessoal e nao sobe.** Nao versione, nao cole conteudo
  em issue, PR ou resposta publica. So `exemplo-*.json` e `_modelo.json` sao
  publicos.
- Rode `python -m pytest tests/ -q` antes de dar qualquer coisa por pronta.
- Mudou uma regra de negocio? Ela provavelmente esta em tres lugares: o script, o
  teste e `viagens/_esquema.md`. Os tres andam juntos.
- Achou uma armadilha nova? Registre em `BACKLOG.md`, secao **Verificado em
  campo**, com a data. E o que impede a proxima sessao de repetir a descoberta.
