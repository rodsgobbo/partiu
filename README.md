# partiu

**Quanto uma viagem para fora do Brasil custa de verdade, em reais, e o que voce
precisa para embarcar.**

Site de viagem mostra o preco da passagem e do hotel, muitas vezes em dolar ou
euro, e para por ai. Ficam de fora justamente as coisas que decidem se a viagem
cabe no bolso:

- o imposto e a taxa do banco quando voce paga em moeda estrangeira;
- se e melhor pagar no cartao, levar dinheiro vivo ou usar conta global;
- a taxa que a cidade cobra por noite de hotel;
- se o pais pede visto, e quanto tempo ele demora para sair;
- se o pais pede vacina de febre amarela de quem vem do Brasil;
- se a escala barata que o site achou exige um visto que voce nao tem.

O partiu cuida dessa parte. Ele **nao procura passagem nem hotel** - isso outros
sites ja fazem bem. Ele pega os precos que voce encontrou e faz a conta brasileira.

## Para quem serve

**Serve** se voce esta planejando uma viagem internacional, quer saber o custo
total em reais sem surpresa e topa colar alguns comandos no terminal (a tela preta
de digitar comandos do computador).

**Nao serve** se voce quer um buscador de passagens. Nao tem um aqui, de proposito.

Voce **nao precisa saber programar**. O passo a passo abaixo parte do zero.

## O que voce precisa ter instalado

So o **Python, versao 3.9 ou mais nova**. Nao ha mais nada para instalar.

Para ver se voce ja tem, abra o terminal e digite:

```bash
python --version
```

Se aparecer `Python 3.9` ou um numero maior, esta pronto.

O [Claude Code](https://claude.com/claude-code) e **opcional**. Com ele, voce
conversa em portugues e ele roda tudo por voce. Sem ele, voce mesmo roda os
comandos abaixo.

## Primeiro uso, em 6 passos

Baixe o projeto e entre na pasta:

```bash
git clone https://github.com/rodsgobbo/partiu.git
cd partiu
```

**1. Veja quanto uma moeda custa hoje**, ja com imposto e taxa do banco. E o jeito
mais rapido de entender para que o projeto serve. Este exemplo mostra quanto
custam 3.000 euros em reais:

```bash
python .claude/skills/cambio-br/scripts/cambio.py EUR 3000
```

**2. Veja o que cada pais pede** de quem tem passaporte brasileiro. Os codigos
sao as siglas dos paises (PT e Portugal, FR e Franca, JP e Japao):

```bash
python .claude/skills/documentos-br/scripts/visto.py PT FR JP
python .claude/skills/documentos-br/scripts/prazos.py 2027-05-10 --exige-visto
```

O segundo comando conta para tras a partir do dia da ida (aqui, 10/05/2027) e
mostra ate quando voce precisa resolver cada documento.

**3. Crie o arquivo da sua viagem.** Copie o modelo em branco:

```bash
cp viagens/_modelo.json viagens/portugal-2027-05.json
```

Depois abra o arquivo novo num editor de texto e troque os valores pelos da sua
viagem. O guia [`viagens/_esquema.md`](viagens/_esquema.md) explica cada campo, e
[`exemplo-lisboa-2027-03.json`](viagens/exemplo-lisboa-2027-03.json) mostra um
arquivo ja preenchido.

**4. Peca para conferir o arquivo:**

```bash
python conferir.py viagens/portugal-2027-05.json
```

Ele procura coisas que nao batem: um roteiro que discorda das datas, um preco
velho, uma escala num pais que pede visto, uma passagem com bilhetes separados
sem tempo suficiente entre os voos. Ele **nao muda nada no seu arquivo** - so
aponta o problema e onde ele esta. Quem decide o que fazer e voce.

**5. Feche a conta em reais:**

```bash
python .claude/skills/viagem/scripts/consolidar.py viagens/portugal-2027-05.json
```

Ele soma tudo, aplica imposto e taxa do banco, inclui a taxa de hotel da cidade
(e avisa quando fez isso) e termina mostrando as tres coisas que mais pesam no
total. E nelas que vale procurar economia.

Confira (passo 4) **antes** de fechar a conta (passo 5): um total certo em cima de
um roteiro errado continua errado.

**6. Na hora de comprar a passagem**, pergunte se e o momento:

```bash
python veredito.py viagens/portugal-2027-05.json
```

A resposta e uma destas:

| Resposta | Quer dizer |
|---|---|
| **RESERVE** | compre agora |
| **ESPERE** | ainda vale esperar, e ele diz ate quando |
| **MUDE** | do jeito que esta, a viagem nao fecha - por exemplo, o visto nao sai a tempo |
| **SEM VEREDITO** | falta informacao para decidir, e ele diz qual |

Ele sempre diz o motivo. E o prazo do documento manda mais que o preco: esperar a
passagem baratear nao adianta se o visto nao fica pronto a tempo.

## Ou peca para uma IA fazer

Se voce prefere nao mexer no terminal, abra a pasta do projeto no Claude Code e
peca em portugues, por exemplo:

> "planeja uma viagem para Portugal em maio de 2027, somos 2, orcamento de R$ 25 mil"

Depois de baixar o projeto, **feche e abra o Claude Code de novo** - e assim que
ele aprende as instrucoes do projeto. Para outros assistentes de IA, as regras
ficam no [`AGENTS.md`](AGENTS.md).

## Todos os comandos

| Comando | Para que serve |
|---|---|
| `python .claude/skills/cambio-br/scripts/cambio.py USD 3000` | quanto uma quantia em moeda estrangeira custa em reais (156 moedas) |
| `python .claude/skills/documentos-br/scripts/visto.py FR PT JP` | o que cada pais pede do passaporte brasileiro |
| `python .claude/skills/documentos-br/scripts/prazos.py 2027-01-15 --exige-visto` | ate quando resolver cada documento |
| `python conferir.py` | procura problemas em todas as suas viagens de uma vez |
| `python recotar.py` | quais precos ja estao velhos e precisam ser buscados de novo hoje |
| `python veredito.py` | se e hora de comprar a passagem |
| `python .claude/skills/viagem/scripts/consolidar.py viagens/<arquivo>.json` | o total da viagem em reais |
| `python saude.py` | quais informacoes guardadas no projeto estao ficando velhas |
| `python dados/passport-index/atualizar.py` | baixa de novo a lista de vistos |
| `python -m pytest tests/ -q` | roda os testes do projeto (precisa do `pytest`) |

Os comandos de moeda e de lista de vistos usam a internet. O `conferir.py` e os
testes nao usam: eles precisam funcionar mesmo sem conexao.

**Um dos testes falha de proposito quando alguma informacao fica velha.** Regras
de imposto, visto e vacina mudam com o tempo, e cada uma tem uma data para ser
conferida de novo. Quando essa data chega perto, o teste
`test_nenhum_dado_esta_vencido` avisa. Nao e defeito: e o projeto pedindo para
alguem conferir a informacao na fonte. Rode `python saude.py` para ver qual.

## As cinco skills

Skills sao instrucoes que o Claude Code segue quando voce conversa com ele.

| Skill | O que faz |
|---|---|
| `viagem` | organiza o planejamento inteiro, na ordem certa: documento primeiro, preco depois |
| `cambio-br` | converte para reais com imposto e taxa do banco, para cada forma de pagamento |
| `documentos-br` | visto, vacina e seguro para passaporte brasileiro, com prazo |
| `roteiro-orcamento` | monta o roteiro dia a dia dentro do orcamento, e ajuda a escolher bairro e tipo de hospedagem |
| `dado-datado` | garante que todo numero que muda com o tempo tenha fonte e data |

## Suas viagens sao so suas

Os arquivos das suas viagens, em `viagens/`, **nao vao para a internet**. O
projeto e configurado para nunca envia-los junto com o resto (so o modelo e o
exemplo de Lisboa sao publicos). Eles guardam coisas pessoais: destino, datas,
orcamento, situacao do passaporte.

O mesmo vale para as paginas que o projeto gera para voce ler e decidir
(`roteiro-*.html` e `decisoes-*.html`).

## Ferramentas de fora (opcionais)

O partiu funciona sozinho. Estas duas ferramentas so servem para **buscar** preco
de voo e hotel:

| Ferramenta | Como instalar | Licenca |
|---|---|---|
| trvl | baixe o programa e aponte o caminho no arquivo `.mcp.json` | so para uso pessoal |
| travel-hacking-toolkit | `/plugin marketplace add borski/travel-hacking-toolkit` | MIT, uso livre |

Para usar o trvl, copie o arquivo de configuracao de exemplo:

```bash
cp .mcp.json.example .mcp.json
```

Se o computador nao achar o trvl, troque `trvl` no arquivo pelo caminho completo
de onde ele esta instalado. Esse arquivo fica so no seu computador, porque o
caminho e diferente em cada maquina.

O comando `/plugin` nao existe em todo lugar - na extensao do VS Code, por
exemplo, ele nao funciona. O [`BACKLOG.md`](BACKLOG.md), item 0.1, explica como
instalar na mao.

## O que ainda nao esta pronto

- **Vacina:** so cinco destinos estao preenchidos, a partir da lista da
  Organizacao Mundial da Saude de 2022.
- **Seguro viagem:** nenhum destino. So achei afirmacoes de sites que vendem
  seguro, que se contradizem. Seguro so entra com fonte oficial.
- **Prazo de visto e de passaporte:** variam demais para ter um numero geral.
  Aparecem como "nao apurado" no calendario, de proposito, em vez de sumir.
- **Lista de vistos:** a fonte parou de ser atualizada em 01/03/2026. Serve para
  uma primeira olhada; para decidir uma compra, confirme no consulado do pais.
- **Taxa de hotel e regra de escala:** cobrem poucos paises, e as regras ainda nao
  foram conferidas no texto oficial de cada governo.
- **Taxa do seu banco:** o projeto usa um valor padrao chutado. Hoje e a maior
  fonte de erro do total, porque o imposto ficou igual para todas as formas de
  pagamento e a taxa do banco virou o que faz diferenca.
- **Tendencia de preco da passagem:** so aparece depois de alguns dias guardando
  precos. Ela cresce cada vez que alguem roda `trvl watch check`.

O [`BACKLOG.md`](BACKLOG.md) tem a lista completa e a ordem de trabalho.

## Palavras que aparecem aqui

| Palavra | O que e |
|---|---|
| IOF | imposto federal cobrado quando voce troca real por moeda estrangeira. Hoje e 3,5% no cartao, no dinheiro vivo e na conta global |
| spread | a margem que o banco ou a casa de cambio cobra por cima da cotacao oficial |
| PTAX | a cotacao oficial do dolar e de outras moedas, publicada pelo Banco Central |
| conta global | conta em moeda estrangeira, de bancos digitais, que costuma ter spread menor |
| CIVP | o certificado internacional de vacina, pedido por paises que exigem febre amarela |
| eTA / e-visa | autorizacao de entrada pedida pela internet antes da viagem |
| escala ou conexao | a parada num aeroporto no meio do caminho, para trocar de aviao |
| bilhete separado | quando os voos de uma mesma viagem sao comprados em bilhetes diferentes. Se o primeiro atrasar e voce perder o segundo, a companhia do segundo nao tem obrigacao de ajudar |

## Licenca

[MIT](LICENSE): uso livre.
