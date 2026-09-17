"""Contradicoes dentro de um arquivo de viagem: o que um bloco diz e outro nega.

Irmao do `saude.py`. Aquele cuida de `dados/` e pergunta se o dado envelheceu;
este cuida de `viagens/` e pergunta se o arquivo concorda consigo mesmo.

Existe porque os cinco defeitos encontrados na primeira viagem real tinham todos a
mesma forma - uma decisao registrada que o roteiro contradizia, uma faixa de
orcamento que esquecia uma linha do proprio orcamento, noites que nao fechavam com
as datas - e nenhum foi achado por ferramenta. Todos apareceram porque uma pessoa
leu os dois lados e reparou.

So le e relata. Corrigir e decisao de quem planeja: uma correcao automatica
apagaria a razao registrada na decisao, que e a parte que custou mais caro.

Uso:
    python conferir.py                    # varre viagens/
    python conferir.py viagens/x.json     # confere um arquivo
    python conferir.py --quieto           # so o codigo de saida, para hook ou CI
"""
import argparse, json, re, sys
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).parent
VIAGENS = RAIZ / "viagens"


class Divergencia:
    """Uma contradicao, com o campo onde mora e os dois valores que discordam.

    O campo nao e enfeite: relatorio que diz o que esta errado sem dizer onde
    obriga quem le a caçar, e quem caça duas vezes para de rodar a ferramenta.
    """

    def __init__(self, familia, campo, mensagem, valores=()):
        self.familia = familia
        self.campo = campo
        self.mensagem = mensagem
        self.valores = tuple(valores)

    def __str__(self):
        base = f"{self.campo}: {self.mensagem}"
        return base + (f" ({' x '.join(str(v) for v in self.valores)})"
                       if self.valores else "")


def arquivos_de_viagem(alvo=None):
    """Os arquivos a conferir. Sem alvo, varre `viagens/*.json`."""
    if alvo is not None:
        return [Path(alvo)]
    if not VIAGENS.is_dir():
        return []
    return sorted(VIAGENS.glob("*.json"))


def relativo(caminho: Path) -> str:
    """Caminho relativo a raiz quando der, para o relatorio caber na linha."""
    try:
        return str(caminho.resolve().relative_to(RAIZ.resolve()))
    except ValueError:
        return str(caminho)


def ler(caminho: Path) -> dict:
    """Abre somente para leitura. Nao ha caminho de escrita neste modulo."""
    return json.loads(caminho.read_text(encoding="utf-8"))


# --- calendario derivado ----------------------------------------------------
# Dia 1 e a ida. Nenhuma data ISO nova entra no roteiro: duplicar as datas criaria
# dois campos dizendo a mesma coisa, e o defeito que este modulo procura e
# exatamente dois campos que discordaram.
#
# `dias` LOCALIZA um bloco no calendario; `noites` CONTA. Sao papeis diferentes de
# proposito. Nenhuma convencao de intervalo fecha para os quatro blocos da viagem
# real ao mesmo tempo: com `fim - inicio + 1`, tres batem e o quarto da 5 contra
# as 4 declaradas. Contar por `dias` faria o derivador escolher uma convencao e,
# com ela, silenciar justo a divergencia que precisa acusar.


def dias_do_bloco(bloco: dict) -> list:
    """Os numeros de dia que um bloco ocupa. `"2-8"` vira [2..8], `"8"` vira [8]."""
    bruto = str(bloco.get("dias", "")).strip()
    if not bruto:
        return []
    partes = bruto.split("-")
    try:
        nums = [int(x) for x in partes]
    except ValueError:
        return []
    if len(nums) == 1:
        return nums
    return list(range(nums[0], nums[-1] + 1))


def data_do_dia(ida, n: int):
    """Dia 1 e a ida; dia N e `ida + N - 1`."""
    return ida + timedelta(days=n - 1)


def datas_do_bloco(bloco: dict, ida) -> list:
    return [data_do_dia(ida, n) for n in dias_do_bloco(bloco)]


def e_cidade(bloco: dict) -> bool:
    """Bloco de estadia tem cidade e noites; bloco de deslocamento tem trecho."""
    return "cidade" in bloco


def noites_declaradas(v: dict) -> int:
    return sum(b.get("noites", 0) for b in v.get("roteiro", []) if e_cidade(b))


def noites_do_intervalo(ida, volta, dia_da_chegada: int) -> int:
    """Noites entre pousar e a vespera do voo de volta.

    A ultima noite fora e sempre a vespera da volta. A primeira depende de quando
    o aviao pousa - e por isso que este parametro existe em vez de uma constante.
    """
    chegada = data_do_dia(ida, dia_da_chegada)
    ultima = volta - timedelta(days=1)
    return (ultima - chegada).days + 1


def chegada_confirmada(v: dict) -> bool:
    """A data de pouso ja esta resolvida?

    O sinal vem do orcamento em vez de um campo proprio porque ja esta la e nao
    sai de sincronia: no dia em que a passagem for comprada, alguem preenche o
    valor, e a data de pouso deixa de ser hipotese sozinha.

    Sem NENHUMA linha de passagem, a resposta e sim - nao ha voo cujo horario
    esteja em aberto. Tratar a ausencia como duvida inventaria ambiguidade numa
    viagem de carro, e ambiguidade inventada e ruido que gasta o alarme.
    """
    voo = [c for c in v.get("custos", [])
           if any(t in c.get("item", "").lower() for t in ("passagem", "voo", "aerea"))]
    if not voo:
        return True
    return all(c.get("valor") is not None for c in voo)


def chegadas_possiveis(v: dict) -> list:
    """Os dias em que o aviao pode pousar.

    Com a passagem comprada e um so: o que o roteiro diz. Sem ela, o horario do
    voo ainda nao existe, e um voo longo que parte de manha pousa um dia antes do
    que um que parte de noite. Devolver os dois e o unico jeito honesto - eleger
    um faria a contagem de noites parecer fechada quando nao esta, e noite de
    hotel a menos so aparece no balcao.
    """
    roteiro = v.get("roteiro", [])
    if not roteiro:
        return []
    dias = dias_do_bloco(roteiro[0])
    if not dias:
        return []
    nominal = dias[-1] if not e_cidade(roteiro[0]) else dias[0]
    if chegada_confirmada(v):
        return [nominal]
    return [nominal, nominal + 1]


def data_de_visita(v: dict, item: dict):
    """Primeiro dia da cidade onde o item acontece, ou None se nao der para saber."""
    cidade = item.get("cidade")
    if not cidade:
        return None
    ida = date.fromisoformat(v["datas"]["ida"])
    for b in v.get("roteiro", []):
        if e_cidade(b) and b.get("cidade") == cidade:
            datas = datas_do_bloco(b, ida)
            return datas[0] if datas else None
    return None


def data_de_compra(v: dict, item: dict):
    """A data de compra sai da visita menos a janela, nunca de um numero fixo."""
    if "janela_dias" not in item:
        return None
    visita = data_de_visita(v, item)
    if visita is None:
        return None
    return visita - timedelta(days=int(item["janela_dias"]))


# --- checagens de calendario ------------------------------------------------


def noites_fecham(v: dict) -> list:
    """As noites do roteiro contra o que o intervalo da viagem comporta."""
    if not v.get("roteiro"):
        return []
    ida = date.fromisoformat(v["datas"]["ida"])
    volta = date.fromisoformat(v["datas"]["volta"])
    declaradas = noites_declaradas(v)
    chegadas = chegadas_possiveis(v)
    if not chegadas:
        return []

    possiveis = {c: noites_do_intervalo(ida, volta, c) for c in chegadas}
    contagens = sorted(set(possiveis.values()))
    faixa = " ou ".join(str(n) for n in contagens)

    # Bater com UMA das hipoteses nao e fechar a conta. Enquanto o pouso admite
    # mais de uma data, a hospedagem esta dimensionada num palpite - e calar
    # porque o palpite casou seria eleger uma hipotese, que e o que o requisito
    # proibe. Uma noite a menos so aparece no balcao do hotel.
    if len(contagens) == 1 and declaradas == contagens[0]:
        return []

    detalhe = ", ".join(f"pousando dia {c}, {n} noites" for c, n in sorted(possiveis.items()))
    if declaradas in contagens:
        d = Divergencia(
            "calendario", "roteiro[].noites",
            "o pouso ainda admite mais de uma data, entao a contagem nao esta fechada",
            (f"{declaradas} declaradas", f"{faixa} possiveis"))
        d.correcao = (f"{detalhe}. Comprar a passagem fecha o numero; ate la, a linha "
                      f"de hospedagem esta dimensionada na hipotese de {declaradas}.")
    else:
        d = Divergencia(
            "calendario", "roteiro[].noites",
            "a soma das noites nao fecha com o intervalo da viagem",
            (f"{declaradas} declaradas", f"{faixa} pelo calendario"))
        d.correcao = (f"acertar as noites do roteiro para {faixa} ({detalhe}), "
                      f"ou rever as datas de ida e volta.")
    return [d]


def hospedagem_bate_com_o_roteiro(v: dict) -> list:
    """A linha de hospedagem contra a soma das noites do roteiro.

    E a linha que vira reserva de verdade, entao errar aqui nao e erro de
    planilha: e chegar no hotel com uma noite a menos que o roteiro previa.
    """
    if not v.get("roteiro"):
        return []
    linhas = [c for c in v.get("custos", []) if "hospedagem" in c.get("item", "").lower()]
    if not linhas:
        return []
    declaradas = noites_declaradas(v)
    achados = []
    for c in linhas:
        if "noites" not in c:
            d = Divergencia("calendario", f"custos[{c['item'][:30]}]",
                            "hospedagem sem numero de noites: nao da para conferir "
                            "contra o roteiro")
            d.correcao = (f"declarar `noites` nesta linha. O roteiro soma {declaradas}.")
            achados.append(d)
        elif c["noites"] != declaradas:
            d = Divergencia("calendario", f"custos[{c['item'][:30]}].noites",
                            "a hospedagem orca um numero de noites que o roteiro nao tem",
                            (f"{c['noites']} na linha de custo", f"{declaradas} no roteiro"))
            d.correcao = "acertar os dois para o mesmo numero antes de reservar."
            achados.append(d)
    return achados


def roteiro_respeita_bloqueios(v: dict) -> list:
    """Deslocamento em data travada, bloqueio sem procedencia, cidades sobrepostas.

    A sobreposicao so vale entre blocos de CIDADE. Trecho dividindo o dia com a
    cidade vizinha e o normal de um dia de viagem - sair de uma cidade e chegar
    na seguinte no mesmo dia 8 nao e conflito, e o proprio dia 8.
    """
    achados = []
    ida = date.fromisoformat(v["datas"]["ida"])
    bloqueios = {}
    for b in v.get("datas_bloqueadas", []):
        if not b.get("decisao"):
            d = Divergencia("calendario", f"datas_bloqueadas[{b.get('data')}]",
                            "data travada sem dizer qual decisao a travou")
            d.correcao = ("nomear a decisao de origem. Bloqueio sem procedencia e "
                          "indistinguivel de bloqueio inventado.")
            achados.append(d)
        try:
            bloqueios[date.fromisoformat(b["data"])] = b
        except (KeyError, ValueError):
            continue

    for bloco in v.get("roteiro", []):
        if e_cidade(bloco):
            continue
        for dia in datas_do_bloco(bloco, ida):
            if dia in bloqueios:
                b = bloqueios[dia]
                d = Divergencia("calendario", f"roteiro[{bloco.get('trecho')}]",
                                "deslocamento marcado numa data que uma decisao travou",
                                (dia.isoformat(), b.get("razao", "sem razao")))
                d.correcao = (f"a decisao que travou esse dia foi: {b.get('decisao')}. "
                              f"Mover o trecho, ou desfazer a decisao por escrito.")
                achados.append(d)

    # Dia com deslocamento e dia de transicao: estar em duas cidades nele e o
    # normal de sair de uma e chegar na outra. Sem trecho no dia, duas cidades
    # significam que voce dorme em duas ao mesmo tempo, e isso e conflito.
    dias_de_trecho = {dia for b in v.get("roteiro", []) if not e_cidade(b)
                      for dia in datas_do_bloco(b, ida)}
    ocupacao = {}
    for bloco in v.get("roteiro", []):
        if not e_cidade(bloco):
            continue
        for dia in datas_do_bloco(bloco, ida):
            ocupacao.setdefault(dia, []).append(bloco.get("cidade"))
    for dia, nomes in sorted(ocupacao.items()):
        distintas = list(dict.fromkeys(nomes))
        if len(distintas) > 1 and dia not in dias_de_trecho:
            d = Divergencia("calendario", f"roteiro[{dia.isoformat()}]",
                            "duas cidades no mesmo dia, e nao ha deslocamento entre elas",
                            tuple(distintas))
            d.correcao = ("ajustar `dias` para os blocos nao se sobreporem, ou "
                          "declarar o trecho que liga as duas.")
            achados.append(d)
    return achados


# Palavras que denunciam uma decisao que TRAVA um dia, e nao apenas o menciona.
# E heuristica, nao leitura: nao ha como saber a intencao de uma frase. Por isso a
# lista e curta e o vies e o silencio - alarme que dispara em toda decisao com data
# seria descartado na primeira semana, e ai o alarme util morre junto.
VOCABULARIO_DE_BLOQUEIO = ("feriado", "lota", "fecha", "evitar", "bloquea", "cheio")


def decisao_virou_dado(v: dict) -> list:
    """Decisao que trava um dia e nunca virou `datas_bloqueadas[]`.

    E o defeito que originou esta conferencia: duas decisoes da primeira viagem
    real moveram trem e passeio para fugir de um feriado, ficaram registradas em
    prosa, e o roteiro seguiu na data antiga porque nada olhava os dois lados.
    """
    ida = date.fromisoformat(v["datas"]["ida"])
    volta = date.fromisoformat(v["datas"]["volta"])
    bloqueadas = set()
    for b in v.get("datas_bloqueadas", []):
        try:
            bloqueadas.add(date.fromisoformat(b["data"]))
        except (KeyError, ValueError):
            continue

    achados = []
    for i, texto in enumerate(v.get("decisoes", [])):
        if not isinstance(texto, str):
            continue
        baixo = texto.lower()
        if not any(p in baixo for p in VOCABULARIO_DE_BLOQUEIO):
            continue
        citadas = set()
        for dd, mm, aaaa in re.findall(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{4}))?\b", texto):
            for ano in ({int(aaaa)} if aaaa else {ida.year, volta.year}):
                try:
                    alvo = date(ano, int(mm), int(dd))
                except ValueError:
                    continue
                if ida <= alvo <= volta:
                    citadas.add(alvo)
        if citadas and not (citadas & bloqueadas):
            d = Divergencia(
                "calendario", f"decisoes[{i}]",
                "decisao trava um dia da viagem e nunca virou dado conferivel",
                (", ".join(x.isoformat() for x in sorted(citadas)),
                 "nenhuma em datas_bloqueadas"))
            d.correcao = (f"registrar em `datas_bloqueadas[]` o dia que esta decisao "
                          f"trava, com a razao e esta decisao como origem. Texto: "
                          f"\"{texto[:80]}...\"")
            achados.append(d)
    return achados


SEMANA = ("segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo")


def janela_de_compra_fecha(v: dict) -> list:
    """A data de compra derivada do roteiro contra a que o arquivo fixou.

    Fixar a data a mao e o defeito: mudar o roteiro um dia move a visita, e a data
    de compra fica para tras sem ninguem notar. Em item que so vende numa janela e
    nao tem segunda chance, isso e a diferenca entre entrar e nao entrar.
    """
    achados = []
    for item in v.get("itens_com_prazo", []):
        nome = item.get("item", "?")
        critico = bool(item.get("critico"))
        visita = data_de_visita(v, item)

        if critico and visita is None:
            d = Divergencia("janela de compra", f"itens_com_prazo[{nome[:30]}]",
                            "item critico sem data de visita: a data de compra nao "
                            "pode ser derivada")
            d.correcao = ("declarar `cidade` do item e garantir que essa cidade tem "
                          "bloco no roteiro.")
            achados.append(d)
            continue

        derivada = data_de_compra(v, item)
        fixada = item.get("data_compra")
        if derivada and fixada:
            try:
                if date.fromisoformat(fixada) != derivada:
                    d = Divergencia("janela de compra", f"itens_com_prazo[{nome[:30]}]",
                                    "a data de compra fixada nao corresponde a visita "
                                    "no roteiro",
                                    (f"{fixada} fixada", f"{derivada.isoformat()} derivada"))
                    d.correcao = ("apagar a data fixa e deixar a janela derivar do "
                                  "roteiro, ou acertar o roteiro.")
                    achados.append(d)
            except ValueError:
                pass

        restritos = [s.lower() for s in item.get("dias_restritos", [])]
        if visita and restritos and SEMANA[visita.weekday()] in restritos:
            d = Divergencia("janela de compra", f"itens_com_prazo[{nome[:30]}]",
                            "visita cai num dia que o proprio item declara restrito",
                            (visita.isoformat(), SEMANA[visita.weekday()]))
            d.correcao = ("mover a visita para outro dia; a data de compra anda junto, "
                          "porque e derivada dela.")
            achados.append(d)
    return achados


# --- checagens de orcamento -------------------------------------------------

# Uma faixa em reais escrita em prosa: "R$ 3.000 a 4.500", "30 mil a 40 mil".
FAIXA = re.compile(
    r"R?\$?\s*([\d][\d.,]*)\s*(mil)?\s*(?:a|ate|-|—)\s*R?\$?\s*([\d][\d.,]*)\s*(mil)?",
    re.IGNORECASE)


def numero_br(bruto: str, mil: bool) -> float:
    """`7.000` e `7,5` em portugues; `mil` multiplica."""
    limpo = bruto.replace(".", "").replace(",", ".")
    return float(limpo) * (1000 if mil else 1)


def faixa_declarada(texto: str):
    """(min, max) de uma faixa em prosa, ou None se nao houver duas pontas."""
    if not isinstance(texto, str):
        return None
    m = FAIXA.search(texto)
    if not m:
        return None
    a, mil_a, b, mil_b = m.groups()
    # "30 mil a 40 mil" costuma abreviar a primeira ponta: "R$ 30 a 40 mil".
    lo = numero_br(a, bool(mil_a) or bool(mil_b))
    hi = numero_br(b, bool(mil_b))
    return (lo, hi) if lo <= hi else (hi, lo)


_CAMBIO = None


def cambio_do_projeto():
    """O `cambio.py`, dono da formula de conversao e das regras de custo.

    A conferencia ja teve a propria conta - `(1 + spread) * (1 + taxa)` - ao lado da
    canonica. Era a copia que a regra do projeto proibe, com um nome de variavel
    diferente o bastante para o teste de formula unica nao reconhecer.
    """
    global _CAMBIO
    if _CAMBIO is None:
        import importlib.util
        caminho = RAIZ / ".claude" / "skills" / "cambio-br" / "scripts" / "cambio.py"
        spec = importlib.util.spec_from_file_location("cambio", caminho)
        _CAMBIO = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_CAMBIO)
    return _CAMBIO


def parametros_de_cambio(v: dict):
    """(spread, iof) lidos do disco - a conferencia nao acessa rede.

    Sem aliquota legivel devolve None, e a faixa sai sem carga: melhor uma faixa
    declaradamente crua que uma com imposto inventado.
    """
    cb = cambio_do_projeto()
    spread = v.get("spread")
    if spread is None:
        spread = cb.SPREAD_PADRAO["cartao"]
    try:
        taxa = cb.iof()["aliquotas"]["cartao_credito_internacional"]["valor"]
    except (OSError, KeyError, ValueError, TypeError):
        return None
    if not isinstance(taxa, (int, float)):
        return None
    return spread, taxa


def faixa_do_orcamento(v: dict):
    """A faixa em reais que as linhas de custo sustentam, e o que ficou de fora.

    Devolve (min, max, fora), onde `fora` sao as linhas que nao entraram e por que.
    Linha em reais entra sempre; em moeda estrangeira depende de cotacao
    registrada. Recusar a faixa inteira por causa de uma linha esconderia o que ja
    da para saber, entao a recusa e por linha e o relatorio diz o que faltou.

    `estimativa` e o TOTAL da linha, antes de `por_pessoa`. Se ela trouxer um preco
    unitario - uma diaria, por exemplo - a faixa sai baixa e calada, que e o modo
    de falha que esta conferencia existe para eliminar. Quando a linha declara
    `noites`, a estimativa e entendida como diaria e multiplicada.
    """
    o = v.get("orcamento", {}) or {}
    cotacoes = o.get("cotacoes", {}) or {}
    pessoas = v.get("viajantes", 1)
    params = parametros_de_cambio(v)
    cb = cambio_do_projeto()
    moeda_local = v.get("moeda_local")
    achada = cb.sobretaxa_do_destino((v.get("destino") or {}).get("pais", ""))
    sobretaxa = achada[0] if achada else 0.0
    lo = hi = 0.0
    fora = []
    for c in v.get("custos", []):
        nome = c.get("item", "?")
        mult = pessoas if c.get("por_pessoa") else 1
        if c.get("valor") is None:
            faixa = faixa_declarada(c.get("estimativa", ""))
            if faixa is None:
                # Duas causas, dois consertos: faltar a estimativa pede escrever
                # uma; ter uma sem duas pontas pede reescrever. Mensagem unica
                # obrigaria quem le a abrir o arquivo para descobrir qual.
                if not c.get("estimativa"):
                    fora.append((nome, "sem estimativa: a faixa calculada esta incompleta"))
                else:
                    fora.append((nome, "estimativa sem minimo e maximo: nao entra na faixa"))
                continue
            noites = c.get("noites")
            if isinstance(noites, int) and noites > 0:
                mult *= noites
            lo += faixa[0] * mult
            hi += faixa[1] * mult
            continue
        moeda = c.get("moeda", "BRL")
        if moeda == "BRL":
            lo += c["valor"] * mult
            hi += c["valor"] * mult
        elif moeda in cotacoes:
            valor = c["valor"] * mult
            if params is None:
                brl = valor * cotacoes[moeda]
            else:
                # Mesma regra do consolidar, pela mesma formula: a sobretaxa e do
                # destino e incide no gasto na moeda de la. Se a faixa e o total
                # usassem regras diferentes, os dois numeros divergiriam.
                sob = sobretaxa if moeda == moeda_local else 0.0
                brl = cb.em_reais(valor, cotacoes[moeda], params[0], params[1], sob)
            lo += brl
            hi += brl
        else:
            fora.append((nome, f"sem cotacao registrada para {moeda}"))
    return lo, hi, fora


def orcamento_fecha(v: dict) -> list:
    """A faixa calculada contra a que o arquivo declara, e o que ficou de fora."""
    if "custos" not in v:
        return []
    achados = []
    o = v.get("orcamento", {}) or {}

    if not v["custos"]:
        d = Divergencia("orcamento", "custos[]",
                        "o arquivo nao tem custo algum a somar")
        d.correcao = "trazer o orcamento para custos[], que e o unico lugar lido."
        achados.append(d)
        return achados

    lo, hi, fora = faixa_do_orcamento(v)
    for nome, motivo in fora:
        d = Divergencia("orcamento", f"custos[{nome[:30]}]",
                        f"linha fora da faixa calculada: {motivo}")
        d.correcao = ("declarar a estimativa como faixa numerica em reais, ou "
                      "registrar a cotacao em orcamento.cotacoes.")
        achados.append(d)

    declarada = faixa_declarada(o.get("ponto_de_ruptura", ""))
    if declarada:
        dl, dh = declarada
        if abs(dl - lo) > 1 or abs(dh - hi) > 1:
            d = Divergencia(
                "orcamento", "orcamento.ponto_de_ruptura",
                "a faixa declarada nao bate com a soma das linhas de custo",
                (f"R$ {dl:,.0f} a {dh:,.0f} declarada",
                 f"R$ {lo:,.0f} a {hi:,.0f} pelas linhas"))
            d.correcao = (f"recalcular a faixa a partir de custos[]. Diferenca no piso: "
                          f"R$ {lo - dl:+,.0f}; no teto: R$ {hi - dh:+,.0f}.")
            achados.append(d)

    informado = o.get("informado_brl")
    if isinstance(informado, (int, float)) and lo > informado:
        d = Divergencia("orcamento", "orcamento.informado_brl",
                        "o piso da faixa ja estoura o orcamento informado",
                        (f"R$ {informado:,.0f} informado", f"R$ {lo:,.0f} de piso"))
        d.correcao = (f"estouro de R$ {lo - informado:,.0f} no melhor caso "
                      f"({(lo / informado - 1) * 100:.0f}%). Rever o teto ou cortar linha.")
        achados.append(d)

    soltos = [(k, x) for k, x in (o.get("linhas_brl") or {}).items()
              if isinstance(x, (int, float))]
    for k, x in soltos:
        d = Divergencia("orcamento", f"orcamento.linhas_brl.{k}",
                        "valor de custo fora de custos[], que ninguem soma", (x,))
        d.correcao = "mover para custos[] ou apagar; duas contabilidades divergem."
        achados.append(d)
    return achados


def sobretaxa_chegou_no_orcamento(v: dict) -> list:
    """Sobretaxa registrada nos dados que nao acha onde incidir.

    O `consolidar.py` aplica a sobretaxa do destino sozinho, a partir de `dados/`,
    sobre as linhas na moeda local. Entao o que ainda pode ficar parado num arquivo
    que ninguem soma nao e a sobretaxa em si: e a de um destino cuja viagem nao tem
    linha nenhuma na moeda de la para ela cair. Acusar a outra coisa - como esta
    checagem fazia antes da Fase 4 - seria alarme permanente sobre algo que ja esta
    no total.
    """
    pais = (v.get("destino") or {}).get("pais")
    if not pais:
        return []
    achado = cambio_do_projeto().sobretaxa_do_destino(pais)
    if achado is None:
        return []
    valor, arquivo, _ = achado
    moeda_local = v.get("moeda_local")
    com_preco_local = [c for c in v.get("custos", [])
                       if c.get("valor") is not None and c.get("moeda") == moeda_local]
    if moeda_local and com_preco_local:
        return []
    motivo = ("o arquivo nao declara `moeda_local`" if not moeda_local
              else f"nenhuma linha com preco em {moeda_local}")
    d = Divergencia(
        "orcamento", f"dados[{arquivo}]",
        f"o destino cobra sobretaxa de {valor:.0%} e ela nao tem onde incidir",
        (motivo,))
    d.correcao = (f"a regra esta em {arquivo}. Declarar `moeda_local` e orcar o gasto "
                  f"no destino nessa moeda, para o consolidar aplicar a sobretaxa.")
    return [d]


# Cada familia de checagem entra aqui. A lista existe para o relatorio saber a
# diferenca entre "conferi e nao achei nada" e "nao conferi nada" - dizer "nada se
# contradiz" sem ter olhado e o mesmo defeito do total que saia zero em silencio.
FAMILIAS = [noites_fecham, hospedagem_bate_com_o_roteiro, roteiro_respeita_bloqueios,
            decisao_virou_dado, janela_de_compra_fecha, orcamento_fecha,
            sobretaxa_chegou_no_orcamento]


def conferir(v: dict) -> list:
    """Todas as familias de checagem sobre uma viagem ja carregada."""
    achados = []
    for familia in FAMILIAS:
        achados.extend(familia(v))
    return achados


def relatar(caminho: Path, achados: list) -> list:
    """As linhas do relatorio de um arquivo, agrupadas por familia.

    Agrupar importa porque as familias pedem acoes diferentes: calendario se
    resolve mexendo no roteiro, orcamento mexendo em `custos[]`. Uma lista corrida
    obriga quem le a fazer esse agrupamento de cabeca toda vez.
    """
    linhas = [f"conferido: {relativo(caminho)}"]
    if not achados:
        linhas.append("  sem contradicao" if FAMILIAS
                      else "  NADA FOI CONFERIDO: nenhuma familia de checagem registrada")
        return linhas
    for familia in dict.fromkeys(d.familia for d in achados):
        linhas.append(f"  {familia}")
        for d in (x for x in achados if x.familia == familia):
            linhas.append(f"    - {d}")
            # A correcao sai como texto e nunca e aplicada: reescrever o arquivo
            # apagaria a razao registrada na decisao, que e a parte cara.
            if getattr(d, "correcao", None):
                linhas.append(f"      correcao sugerida: {d.correcao}")
    return linhas


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("arquivo", nargs="?", help="um arquivo; sem isto, varre viagens/")
    p.add_argument("--quieto", action="store_true", help="so o codigo de saida")
    p.add_argument("--saida", metavar="ARQUIVO",
                   help="nao suportado: o relatorio so vai para a saida padrao")
    a = p.parse_args()

    # O relatorio repete destino, datas, orcamento e decisoes de quem viaja. Gravar
    # isso em arquivo e como esse arquivo nasce fora do .gitignore e sobe junto com
    # o codigo. Quem quiser um arquivo redireciona a saida e assume a escolha.
    if a.saida:
        print("--saida nao e suportado: o relatorio carrega dado pessoal de viagem,",
              file=sys.stderr)
        print("e arquivo criado por ferramenta nasce fora do .gitignore.",
              file=sys.stderr)
        print("Se for mesmo o que voce quer: python conferir.py > seu-arquivo.txt",
              file=sys.stderr)
        return 2

    alvos = arquivos_de_viagem(a.arquivo)
    if not alvos:
        # "Nao existe" e "nada a conferir" pedem acoes diferentes: um e caminho
        # errado, o outro e viagem que ainda nao foi criada. Os dois falham, mas
        # o relatorio precisa dizer qual dos dois foi.
        onde = a.arquivo or relativo(VIAGENS)
        print(f"Nada foi conferido: {onde} nao tem arquivo de viagem.", file=sys.stderr)
        return 1

    total = 0
    for caminho in alvos:
        if not caminho.is_file():
            print(f"Nao consegui ler {relativo(caminho)}: arquivo nao existe.",
                  file=sys.stderr)
            return 1
        try:
            v = ler(caminho)
        except json.JSONDecodeError as e:
            print(f"Nao consegui ler {relativo(caminho)}: JSON invalido, "
                  f"linha {e.lineno}, coluna {e.colno}.", file=sys.stderr)
            return 1
        except OSError as e:
            print(f"Nao consegui ler {relativo(caminho)}: {e.strerror}.", file=sys.stderr)
            return 1
        achados = conferir(v)
        total += len(achados)
        if not a.quieto:
            for linha in relatar(caminho, achados):
                print(linha)

    if not a.quieto:
        print()
        if not FAMILIAS:
            print("NENHUMA CHECAGEM REGISTRADA. Este relatorio nao prova nada.")
        elif total:
            print(f"{len(alvos)} arquivo(s) conferido(s), {total} contradicao(oes).")
        else:
            print(f"{len(alvos)} arquivo(s) conferido(s). Nada se contradiz.")

    # Sem familia registrada nao ha o que afirmar, entao o codigo de saida acusa:
    # hook e CI passando em verde por falta de checagem e a pior falha possivel.
    return 1 if total or not FAMILIAS else 0


if __name__ == "__main__":
    sys.exit(main())
