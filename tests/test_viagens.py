"""Testes das partes deterministicas. Nenhum toca a rede: cotacao entra como
parametro, para o teste falhar por bug e nunca por internet fora do ar."""
import csv
import importlib.util
import json
from datetime import date, timedelta
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SKILLS = RAIZ / ".claude" / "skills"


def carregar(caminho: Path):
    spec = importlib.util.spec_from_file_location(caminho.stem, caminho)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


consolidar = carregar(SKILLS / "viagem" / "scripts" / "consolidar.py")
visto = carregar(SKILLS / "documentos-br" / "scripts" / "visto.py")
prazos = carregar(SKILLS / "documentos-br" / "scripts" / "prazos.py")


# --- conversao de custo -----------------------------------------------------

def test_valor_em_reais_nao_sofre_iof_nem_conversao():
    """Passagem comprada em BRL numa agencia daqui nao teve operacao de cambio,
    entao aplicar IOF nela inventaria um imposto que nao foi cobrado."""
    c = {"valor": 4200.0, "moeda": "BRL", "por_pessoa": False}
    assert consolidar.linha_em_brl(c, taxa=6.0, spread=0.04, taxa_iof=0.035, pessoas=2) == 4200.0


def test_por_pessoa_multiplica_antes_da_conversao():
    c = {"valor": 100.0, "moeda": "BRL", "por_pessoa": True}
    assert consolidar.linha_em_brl(c, 1.0, 0.0, 0.0, pessoas=3) == 300.0


def test_sem_por_pessoa_nao_multiplica():
    c = {"valor": 100.0, "moeda": "BRL", "por_pessoa": False}
    assert consolidar.linha_em_brl(c, 1.0, 0.0, 0.0, pessoas=3) == 100.0


def test_moeda_estrangeira_aplica_taxa_spread_e_iof_nessa_ordem():
    c = {"valor": 100.0, "moeda": "EUR", "por_pessoa": False}
    obtido = consolidar.linha_em_brl(c, taxa=6.0, spread=0.04, taxa_iof=0.035, pessoas=1)
    assert obtido == pytest.approx(100 * 6.0 * 1.04 * 1.035)


def test_por_pessoa_e_conversao_combinados():
    c = {"valor": 700.0, "moeda": "EUR", "por_pessoa": True}
    obtido = consolidar.linha_em_brl(c, 6.0184, 0.04, 0.035, pessoas=2)
    assert obtido == pytest.approx(9069.49, abs=0.01)


# --- leitura do visto -------------------------------------------------------

def test_numero_de_dias_vira_texto_de_isencao():
    assert visto.descrever("90") == "sem visto, ate 90 dias"


def test_codigos_conhecidos_tem_traducao():
    assert "eletronica" in visto.descrever("eta")
    assert "exigido" in visto.descrever("visa required")


def test_codigo_desconhecido_e_devolvido_cru():
    """Melhor mostrar o valor bruto do dataset que engolir num rotulo errado."""
    assert visto.descrever("algo-novo") == "algo-novo"


def test_envelhecimento_conta_dias():
    ontem = (date.today() - timedelta(days=1)).isoformat()
    assert visto.envelhecimento(ontem) == 1


def test_envelhecimento_com_data_ilegivel_nao_alerta():
    """Preferimos nao alertar a alertar errado."""
    assert visto.envelhecimento("sei la") is None
    assert visto.envelhecimento(None) is None


# --- filtro de prazos -------------------------------------------------------

class Flags:
    def __init__(self, visto=False, civp=False, eta=False):
        self.exige_visto, self.exige_civp, self.exige_eta = visto, civp, eta


def test_item_de_visto_so_aparece_quando_ha_visto():
    item = {"requer": "visto"}
    assert prazos.aplicavel(item, Flags(visto=True))
    assert not prazos.aplicavel(item, Flags(visto=False))


def test_item_sem_requer_aparece_sempre():
    assert prazos.aplicavel({}, Flags())
    assert prazos.aplicavel({"requer": None}, Flags())


def test_filtro_ignora_o_texto_em_prosa():
    """O filtro le `requer`. Se voltar a casar substring em `condicao`, este teste
    cai - foi assim que a versao anterior podia mudar de comportamento so porque
    alguem reescreveu uma frase."""
    item = {"condicao": "quando documentos-br apontar visto exigido"}
    assert prazos.aplicavel(item, Flags(visto=False))


def test_todo_item_de_prazo_declara_requer():
    """Item novo sem `requer` cairia no default 'aparece sempre' em silencio."""
    d = json.loads((RAIZ / "dados" / "prazos.json").read_text(encoding="utf-8"))
    for i in d["itens"]:
        assert "requer" in i, f"{i['id']} sem campo requer"
        assert i["requer"] in (None, "civp", "visto", "eta"), i["id"]


# --- integridade dos dados --------------------------------------------------

def test_todas_as_aliquotas_de_iof_estao_verificadas():
    d = json.loads((RAIZ / "dados" / "iof.json").read_text(encoding="utf-8"))
    assert d["verificado"] is True
    for nome, a in d["aliquotas"].items():
        assert a["verificado"] is True, f"{nome} nao verificada"
        assert isinstance(a["valor"], float), f"{nome} sem valor numerico"
        assert a.get("inciso"), f"{nome} sem inciso do decreto"


def test_iof_declara_que_a_base_juridica_e_instavel():
    """A aliquota vem de liminar pendente de Plenario. Se alguem marcar como
    estavel sem o STF ter julgado, o teste avisa."""
    d = json.loads((RAIZ / "dados" / "iof.json").read_text(encoding="utf-8"))
    sj = d["status_juridico"]
    assert sj["estavel"] is False
    assert sj["reconferir_em"]


def test_dado_de_visto_cobre_o_passaporte_brasileiro():
    """O bug do trvl era exatamente este: BR ausente do dataset."""
    with (RAIZ / "dados" / "passport-index" / "br.csv").open(encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    assert len(linhas) >= 190
    assert all(l["Passport"] == "BR" for l in linhas)


@pytest.mark.parametrize("destino,esperado", [
    ("FR", "90"), ("PT", "90"), ("JP", "90"), ("GB", "eta"), ("US", "visa required"),
])
def test_destinos_conhecidos_batem(destino, esperado):
    with (RAIZ / "dados" / "passport-index" / "br.csv").open(encoding="utf-8") as f:
        m = {l["Destination"]: l["Requirement"] for l in csv.DictReader(f)}
    assert m[destino] == esperado


def test_prazo_sem_valor_traz_instrucao_do_que_fazer():
    """Prazo null nao pode ser so ausencia: precisa dizer onde apurar, senao vira
    um item invisivel no calendario."""
    d = json.loads((RAIZ / "dados" / "prazos.json").read_text(encoding="utf-8"))
    for i in d["itens"]:
        if i["prazo_dias"] is None:
            assert len(i.get("nota", "")) > 40, f"{i['id']} sem instrucao"


def test_todo_dado_perecivel_declara_quando_foi_consultado():
    for nome in ("iof.json", "prazos.json"):
        d = json.loads((RAIZ / "dados" / nome).read_text(encoding="utf-8"))
        assert d.get("consultado_em"), f"{nome} sem consultado_em"


# --- contratos entre arquivos -----------------------------------------------

def test_meios_de_pagamento_apontam_para_chaves_que_existem():
    """O consolidar traduz meio de pagamento em duas chaves, uma no iof.json e
    outra no SPREAD_PADRAO. Se alguem renomear de um lado so, isto cai."""
    cambio = carregar(SKILLS / "cambio-br" / "scripts" / "cambio.py")
    iof = json.loads((RAIZ / "dados" / "iof.json").read_text(encoding="utf-8"))
    for meio, (chave_iof, chave_spread) in consolidar.MEIOS.items():
        assert chave_iof in iof["aliquotas"], f"{meio}: {chave_iof} nao existe no iof.json"
        assert chave_spread in cambio.SPREAD_PADRAO, f"{meio}: {chave_spread} sem spread"


def test_a_formula_de_conversao_e_uma_so():
    """A conta canonica mora no cambio.py. Se o consolidar - ou o conferir - voltar
    a ter a sua propria copia, as duas divergem no primeiro ajuste de aliquota.

    A busca e por padrao, nao por texto exato: o conferir ja teve uma copia com
    `taxa` no lugar de `taxa_iof`, e a versao anterior deste teste nao a viu. A
    mencao entre crases, em docstring que conta essa historia, nao conta."""
    import re
    cambio = carregar(SKILLS / "cambio-br" / "scripts" / "cambio.py")
    assert cambio.em_reais(100.0, 6.0, 0.04, 0.035) == pytest.approx(100 * 6 * 1.04 * 1.035)
    assert cambio.em_reais(100.0, 6.0, 0.04, 0.035, 0.03) == pytest.approx(
        100 * 6 * 1.04 * 1.035 * 1.03), "a sobretaxa nao entrou na composicao canonica"
    copia = re.compile(r"(?<![`\w])\(1 \+ spread\) \* \(1 \+")
    for caminho in (SKILLS / "viagem" / "scripts" / "consolidar.py", RAIZ / "conferir.py"):
        fonte = caminho.read_text(encoding="utf-8")
        assert "em_reais(" in fonte, f"{caminho.name} deixou de usar a formula canonica"
        assert not copia.search(fonte), f"copia da formula voltou em {caminho.name}"


# --- conformidade com a skill dado-datado -----------------------------------
# A disciplina do projeto so vale se for verificavel. Antes destes testes ela era
# prosa num SKILL.md, e os proprios arquivos de dados usavam tres nomes
# diferentes para "quando eu conferi" - o que impedia qualquer checagem.

DADOS = list((RAIZ / "dados").rglob("*.json"))


def test_existem_arquivos_de_dados_para_checar():
    """Guarda contra os testes abaixo passarem por vacuidade."""
    assert len(DADOS) >= 5


@pytest.mark.parametrize("arq", DADOS, ids=lambda p: p.name)
def test_todo_dado_declara_se_foi_verificado(arq):
    d = json.loads(arq.read_text(encoding="utf-8"))
    assert isinstance(d.get("verificado"), bool), f"{arq.name} sem verificado booleano"


@pytest.mark.parametrize("arq", DADOS, ids=lambda p: p.name)
def test_todo_dado_usa_o_nome_canonico_da_data(arq):
    """`consultado_em` e o nome unico. `data_do_dado` pode existir ao lado, mas e
    outro conceito: a data da fonte la em cima, nao a data em que olhamos."""
    d = json.loads(arq.read_text(encoding="utf-8"))
    assert "consultado_em" in d, f"{arq.name} sem consultado_em"
    for proibido in ("data_da_coleta", "baixado_em"):
        assert proibido not in d, f"{arq.name} voltou a usar {proibido}"


@pytest.mark.parametrize("arq", DADOS, ids=lambda p: p.name)
def test_dado_nao_verificado_explica_o_que_falta(arq):
    """Marcar verificado=false sem dizer o que falta deixa a pendencia invisivel:
    ninguem sabe o que precisa ser feito para fechar."""
    d = json.loads(arq.read_text(encoding="utf-8"))
    if d["verificado"] is False:
        texto = d.get("pendencia") or d.get("ressalva") or d.get("ressalva_atualizacao") or ""
        assert len(texto) > 30, f"{arq.name} nao verificado e sem pendencia descrita"


@pytest.mark.parametrize("arq", DADOS, ids=lambda p: p.name)
def test_data_de_consulta_e_legivel_ou_nula_por_escrito(arq):
    """Data ilegivel silencia os alertas de envelhecimento. Null e aceito quando
    ha pendencia declarada; string quebrada, nunca."""
    d = json.loads(arq.read_text(encoding="utf-8"))
    valor = d["consultado_em"]
    if valor is None:
        assert d.get("pendencia"), f"{arq.name}: consultado_em nulo sem pendencia"
    else:
        date.fromisoformat(valor)


# --- saude do projeto -------------------------------------------------------

saude = carregar(RAIZ / "saude.py")


def test_nenhum_dado_esta_vencido():
    """Este teste e um despertador, nao uma invariante de codigo.

    Se ele falhar sem ninguem ter mexido em nada, esta funcionando: significa que
    um dado passou da validade ou que uma reconferencia venceu. A correcao nao e
    afrouxar o teste - e rodar `python saude.py`, ver o que apontou, reconferir na
    fonte e atualizar o JSON. Foi de proposito que ele quebra sozinho com o tempo:
    dado perecivel que nunca reclama e o modo de falha que este projeto existe
    para evitar."""
    _, problemas = saude.dados()
    assert not problemas, "python saude.py explica: " + "; ".join(problemas)


def test_idade_ilegivel_nao_vira_zero():
    """Devolver 0 para data quebrada faria um dado podre passar por novo."""
    assert saude.idade("nao e data") is None
    assert saude.idade(None) is None
    assert saude.idade(date.today().isoformat()) == 0


# --- reconhecer fonte congelada nao pode virar anistia ----------------------
# Fonte que parou de ser atualizada e um caso sem acao possivel: rodar o
# atualizar rebaixa o mesmo CSV. O alarme aprendeu a nao cobrar essa acao - e o
# risco de ensinar isso a ele e criar um jeito de calar qualquer dado velho.
# Estes testes existem para que o reconhecimento custe uma data de volta.

CONGELADAS = [a for a in DADOS if "fonte_congelada" in json.loads(a.read_text(encoding="utf-8"))]


@pytest.mark.parametrize("arq", CONGELADAS, ids=lambda p: p.name)
def test_fonte_congelada_tem_data_para_voltar(arq):
    """Sem `reconferir_em` o bloco silenciaria o alerta para sempre - trocaria um
    alarme barulhento demais por um alarme mudo, que e o modo de falha pior."""
    b = json.loads(arq.read_text(encoding="utf-8"))["fonte_congelada"]
    visto_em = date.fromisoformat(b["reconferido_em"])
    volta_em = date.fromisoformat(b["reconferir_em"])
    assert volta_em > visto_em, f"{arq.name}: reconferir_em nao esta no futuro da conferencia"
    assert (volta_em - visto_em).days <= 366, f"{arq.name}: prazo longo demais para dado de visto"
    assert len(b.get("achado", "")) > 60, f"{arq.name}: sem o achado que justifica o silencio"


def _dados_falsos(pasta: Path, fonte: dict):
    (pasta / "dados").mkdir()
    (pasta / "dados" / "x.json").write_text(
        json.dumps({"verificado": True, "consultado_em": date.today().isoformat(), **fonte}),
        encoding="utf-8")


def test_fonte_velha_sem_reconhecimento_continua_gritando(tmp_path, monkeypatch):
    """O contraprovado do teste seguinte: sem o bloco, o alarme toca."""
    _dados_falsos(tmp_path, {"data_do_dado": "2020-01-01"})
    monkeypatch.setattr(saude, "RAIZ", tmp_path)
    _, problemas = saude.dados()
    assert any("a FONTE tem" in p for p in problemas)


def test_reconhecimento_cala_o_alerta_mas_nao_a_reconferencia_vencida(tmp_path, monkeypatch):
    """Reconhecer troca o alerta por um prazo. Vencido o prazo, volta a doer -
    e volta pelo walker de `reconferir_em`, nao por codigo especial: e o que
    impede o bloco de ser uma anistia permanente."""
    ontem = (date.today() - timedelta(days=1)).isoformat()
    _dados_falsos(tmp_path, {
        "data_do_dado": "2020-01-01",
        "fonte_congelada": {"reconferido_em": "2026-01-01", "reconferir_em": ontem},
    })
    monkeypatch.setattr(saude, "RAIZ", tmp_path)
    _, problemas = saude.dados()
    assert not any("a FONTE tem" in p for p in problemas), "o alerta sem saida deveria calar"
    assert any("reconferencia venceu" in p for p in problemas), "o prazo vencido deveria doer"


atualizar = carregar(RAIZ / "dados" / "passport-index" / "atualizar.py")


def test_fonte_que_volta_a_andar_perde_o_reconhecimento():
    """Se a fonte voltar a ser atualizada, o motivo de calar o alerta morre. O
    bloco tem de sair junto - senao o alerta fica mudo para sempre por uma razao
    que deixou de existir, que e pior que nunca ter reconhecido nada."""
    congelada = {"commit": "9c59780", "fonte_congelada": {"reconferido_em": "2026-09-09"}}
    assert atualizar.descongelou(congelada, "abc1234"), "fonte andou e o bloco ficou"
    assert not atualizar.descongelou(congelada, "9c59780"), "mesmo commit nao e degelo"
    assert not atualizar.descongelou({"commit": "9c59780"}, "abc1234"), "sem bloco, nada a remover"


# --- custos[] e a unica contabilidade ---------------------------------------
# O primeiro uso real guardou o orcamento fora de custos[], o script somou a
# lista vazia e imprimiu TOTAL R$ 0,00 saindo com codigo 0. Numero errado que sai
# calado e o modo de falha que este projeto existe para evitar.

def _viagem(tmp_path, custos):
    """Viagem so em BRL: o consolidar nao busca cotacao, entao o teste nao usa rede."""
    arq = tmp_path / "v.json"
    arq.write_text(json.dumps({
        "destino": {"cidade": "Teste", "pais": "PT"},
        "datas": {"ida": "2027-01-01", "volta": "2027-01-10"},
        "viajantes": 2, "moeda_local": "EUR", "meio_pagamento": "cartao_credito",
        "spread": 0.04, "custos": custos,
    }), encoding="utf-8")
    return str(arq)


def _rodar(caminho, monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["consolidar.py", caminho])
    consolidar.main()
    return capsys.readouterr().out


def test_custos_vazio_e_erro_e_nao_total_zero(tmp_path, monkeypatch, capsys):
    """Somar lista vazia dava 0,00 com cara de resposta. Preferimos parar."""
    with pytest.raises(SystemExit) as e:
        _rodar(_viagem(tmp_path, []), monkeypatch, capsys)
    assert "vazio" in str(e.value)


def test_linha_sem_preco_nao_some_nem_vira_zero(tmp_path, monkeypatch, capsys):
    """`valor: null` e 'conhecido, nao orcado' - some do total, nunca da lista, e
    rebaixa o total a PARCIAL. Some da lista, o piso passaria por total fechado."""
    saida = _rodar(_viagem(tmp_path, [
        {"item": "Hotel", "valor": 1000, "moeda": "BRL", "por_pessoa": False,
         "consultado_em": date.today().isoformat()},
        {"item": "Passagem", "valor": None, "moeda": "BRL", "por_pessoa": True,
         "estimativa": "R$ 7 a 9 mil"},
    ]), monkeypatch, capsys)
    assert "Passagem" in saida, "linha sem preco sumiu da lista"
    assert "R$ 7 a 9 mil" in saida, "a estimativa nao cotada nao apareceu"
    assert "PARCIAL" in saida and "PISO" in saida, "o total nao se declarou parcial"
    assert "1,000.00" in saida
    assert "TOTAL" not in saida, "chamou de TOTAL um numero que falta linha"


def test_total_fechado_nao_se_chama_parcial(tmp_path, monkeypatch, capsys):
    """O contraprovado: sem linha faltando, volta a ser TOTAL."""
    saida = _rodar(_viagem(tmp_path, [
        {"item": "Hotel", "valor": 1000, "moeda": "BRL", "por_pessoa": False,
         "consultado_em": date.today().isoformat()},
    ]), monkeypatch, capsys)
    assert "TOTAL" in saida and "PARCIAL" not in saida and "PISO" not in saida


@pytest.mark.parametrize("arq", sorted((RAIZ / "viagens").glob("*.json")),
                         ids=lambda p: p.name)
def test_viagem_real_tem_o_orcamento_dentro_de_custos(arq):
    """Despertador contra a regressao que originou tudo isto: se alguem voltar a
    guardar dinheiro em orcamento.linhas_brl, o consolidar para de ver.

    Varre o que estiver no disco em vez de nomear um arquivo: viagem real e dado
    pessoal e o .gitignore a mantem fora do repositorio, entao um teste que
    exigisse o arquivo da viagem real quebraria em clone limpo e em CI."""
    v = json.loads(arq.read_text(encoding="utf-8"))
    assert v["custos"], f"{arq.name}: custos[] esvaziou de novo"
    # `orcamento` e o bloco que criou a contabilidade paralela. Nem toda viagem
    # tem um; a que tiver nao pode voltar a guardar dinheiro la dentro.
    soltos = [f"{k}={x}" for k, x in (v.get("orcamento", {}).get("linhas_brl") or {}).items()
              if isinstance(x, (int, float))]
    assert not soltos, f"{arq.name}: valor solto fora de custos[]: {soltos}"


# --- contrato de datas bloqueadas -------------------------------------------
# Decisao continua em prosa em `decisoes[]`; `datas_bloqueadas[]` e o recorte que
# uma ferramenta consegue comparar com o roteiro. Duas decisoes da primeira viagem
# real ficaram registradas e o roteiro seguiu na data antiga por duas semanas -
# nao havia como nada alem de um leitor humano notar.

VIAGENS = sorted((RAIZ / "viagens").glob("*.json"))


def test_algum_arquivo_de_viagem_demonstra_datas_bloqueadas():
    """Guarda contra o teste abaixo passar por vacuidade. Viagem real fica fora do
    git, entao quem sustenta esta garantia num clone limpo e o exemplo publico."""
    com_bloqueio = [a for a in VIAGENS
                    if json.loads(a.read_text(encoding="utf-8")).get("datas_bloqueadas")]
    assert com_bloqueio, "nenhum arquivo de viagem declara datas_bloqueadas"


@pytest.mark.parametrize("arq", VIAGENS, ids=lambda p: p.name)
def test_toda_data_bloqueada_nomeia_a_decisao_de_origem(arq):
    """Bloqueio sem procedencia e indistinguivel de bloqueio inventado, e daqui a
    um ano ninguem lembra por que aquele dia estava travado."""
    v = json.loads(arq.read_text(encoding="utf-8"))
    for i, b in enumerate(v.get("datas_bloqueadas", [])):
        onde = f"{arq.name}[datas_bloqueadas][{i}]"
        date.fromisoformat(b["data"])
        assert b.get("razao"), f"{onde} sem razao"
        assert b.get("decisao"), f"{onde} sem decisao de origem"


@pytest.mark.parametrize("arq", VIAGENS, ids=lambda p: p.name)
def test_data_bloqueada_cai_dentro_da_viagem(arq):
    """Bloquear um dia fora do intervalo da viagem nao protege de nada e esconde um
    erro de digitacao no ano ou no mes."""
    v = json.loads(arq.read_text(encoding="utf-8"))
    ida, volta = date.fromisoformat(v["datas"]["ida"]), date.fromisoformat(v["datas"]["volta"])
    for b in v.get("datas_bloqueadas", []):
        d = date.fromisoformat(b["data"])
        assert ida <= d <= volta, f"{arq.name}: {d} fora de {ida}..{volta}"


# --- contrato de sobretaxa por destino --------------------------------------
# A mesma taxa de 3% estava escrita em dois lugares do china-cuidados.json.
# Regra duplicada nao fica duplicada: fica divergente, no primeiro ajuste.

CUIDADOS = sorted((RAIZ / "dados").glob("*-cuidados.json"))


def test_existem_arquivos_de_cuidados_para_checar():
    assert CUIDADOS, "nenhum arquivo de cuidados de destino"


@pytest.mark.parametrize("arq", CUIDADOS, ids=lambda p: p.name)
def test_cuidados_de_destino_declaram_o_pais(arq):
    """Sem ISO-2 nao ha como ligar o arquivo ao `destino.pais` de uma viagem, e a
    regra de custo fica parada num arquivo que ninguem soma."""
    d = json.loads(arq.read_text(encoding="utf-8"))
    pais = d.get("pais")
    assert isinstance(pais, str) and len(pais) == 2 and pais.isupper(), \
        f"{arq.name}: pais ausente ou fora de ISO-2: {pais!r}"


@pytest.mark.parametrize("arq", CUIDADOS, ids=lambda p: p.name)
def test_sobretaxa_tem_valor_numerico(arq):
    """Aliquota em prosa nao entra em conta. `regra` fica como descricao."""
    d = json.loads(arq.read_text(encoding="utf-8"))
    t = d.get("pagamentos", {}).get("taxa_cross_border")
    if t is None:
        return
    assert isinstance(t.get("valor"), float), f"{arq.name}: sobretaxa sem valor numerico"
    assert 0 <= t["valor"] < 1, f"{arq.name}: valor deve ser decimal, veio {t['valor']}"
    isencao = t.get("isencao")
    if isencao is not None:
        assert isinstance(isencao, dict), f"{arq.name}: isencao precisa ser objeto com validade"
        date.fromisoformat(isencao["valido_ate"])


@pytest.mark.parametrize("arq", CUIDADOS, ids=lambda p: p.name)
def test_aliquota_aparece_uma_vez_so_como_fonte(arq):
    """O texto pode citar o percentual; o que nao pode e um segundo campo se
    passando por fonte. Percentual solto em string vira a copia que diverge."""
    bruto = arq.read_text(encoding="utf-8")
    t = json.loads(bruto).get("pagamentos", {}).get("taxa_cross_border")
    if t is None:
        return
    pct = f"{t['valor'] * 100:g}%"
    fora_da_regra = bruto.count(f'"{pct}"')
    assert fora_da_regra == 0, \
        f"{arq.name}: {pct} aparece {fora_da_regra}x como valor de campo, nao so na prosa"


# --- o conferidor -----------------------------------------------------------

conferir_mod = carregar(RAIZ / "conferir.py")


def _viagem_minima(tmp_path, **extra):
    pasta = tmp_path / "viagens"
    pasta.mkdir(exist_ok=True)
    v = {"destino": {"cidade": "X", "pais": "PT"},
         "datas": {"ida": "2027-03-10", "volta": "2027-03-20"},
         "viajantes": 1, "custos": [], "roteiro": [], **extra}
    arq = pasta / "v.json"
    arq.write_text(json.dumps(v), encoding="utf-8")
    return pasta, arq


def _rodar_conferidor(monkeypatch, pasta, argv):
    monkeypatch.setattr(conferir_mod, "VIAGENS", pasta)
    monkeypatch.setattr("sys.argv", argv)
    return conferir_mod.main()


def test_conferidor_varre_o_diretorio_de_viagens(tmp_path, monkeypatch, capsys):
    pasta, arq = _viagem_minima(tmp_path)
    _rodar_conferidor(monkeypatch, pasta, ["conferir.py"])
    assert "v.json" in capsys.readouterr().out


def test_conferidor_nao_altera_o_arquivo(tmp_path, monkeypatch, capsys):
    """So le. Reescrever apagaria a razao registrada numa decisao."""
    pasta, arq = _viagem_minima(tmp_path)
    antes = arq.read_bytes()
    _rodar_conferidor(monkeypatch, pasta, ["conferir.py"])
    assert arq.read_bytes() == antes


def test_sem_familia_registrada_o_conferidor_nao_diz_que_esta_tudo_bem(tmp_path, monkeypatch, capsys):
    """Relatorio verde por falta de checagem e a pior falha possivel num hook:
    passa despercebido justamente porque parece sucesso."""
    pasta, _ = _viagem_minima(tmp_path)
    monkeypatch.setattr(conferir_mod, "FAMILIAS", [])
    saida_codigo = _rodar_conferidor(monkeypatch, pasta, ["conferir.py"])
    saida = capsys.readouterr().out
    assert saida_codigo != 0
    assert "NADA FOI CONFERIDO" in saida
    assert "Nada se contradiz" not in saida


def test_com_familia_registrada_e_sem_achado_o_codigo_e_zero(tmp_path, monkeypatch, capsys):
    pasta, _ = _viagem_minima(tmp_path)
    monkeypatch.setattr(conferir_mod, "FAMILIAS", [lambda v: []])
    assert _rodar_conferidor(monkeypatch, pasta, ["conferir.py"]) == 0
    assert "Nada se contradiz" in capsys.readouterr().out


def test_achado_faz_o_conferidor_falhar(tmp_path, monkeypatch, capsys):
    pasta, _ = _viagem_minima(tmp_path)
    d = conferir_mod.Divergencia("calendario", "roteiro[0].noites", "nao fecha", (17, 18))
    monkeypatch.setattr(conferir_mod, "FAMILIAS", [lambda v: [d]])
    assert _rodar_conferidor(monkeypatch, pasta, ["conferir.py"]) != 0
    saida = capsys.readouterr().out
    assert "roteiro[0].noites" in saida and "17" in saida and "18" in saida


def test_diretorio_sem_viagem_falha_dizendo_que_nada_foi_conferido(tmp_path, monkeypatch, capsys):
    pasta = tmp_path / "viagens"
    pasta.mkdir()
    assert _rodar_conferidor(monkeypatch, pasta, ["conferir.py"]) != 0
    assert "Nada foi conferido" in capsys.readouterr().err


def test_json_quebrado_falha_apontando_a_linha(tmp_path, monkeypatch, capsys):
    pasta, arq = _viagem_minima(tmp_path)
    arq.write_text('{"datas": ', encoding="utf-8")
    assert _rodar_conferidor(monkeypatch, pasta, ["conferir.py", str(arq)]) != 0
    assert "JSON invalido" in capsys.readouterr().err


def test_pedido_de_relatorio_em_arquivo_e_recusado(tmp_path, monkeypatch, capsys):
    pasta, _ = _viagem_minima(tmp_path)
    alvo = tmp_path / "relatorio.txt"
    assert _rodar_conferidor(monkeypatch, pasta, ["conferir.py", "--saida", str(alvo)]) != 0
    assert "dado pessoal" in capsys.readouterr().err
    assert not alvo.exists(), "o conferidor criou o arquivo que deveria recusar"


# --- fumaca das checagens ---------------------------------------------------
# Cada familia com um caso que acusa e um contraprovado silencioso. Sem o
# contraprovado, uma checagem que sempre dispara passaria por checagem que funciona.

def _viagem_base(**extra):
    return {"destino": {"cidade": "X", "pais": "PT"},
            "datas": {"ida": "2027-03-10", "volta": "2027-03-20"},
            "viajantes": 1, "spread": 0.0,
            "custos": [{"item": "Hotel", "valor": 1000, "moeda": "BRL",
                        "por_pessoa": False, "consultado_em": "2027-01-01"}],
            "roteiro": [{"trecho": "A -> B", "dias": "1-2"},
                        {"cidade": "B", "dias": "2-10", "noites": 9}],
            **extra}


def test_noites_que_fecham_ficam_caladas():
    assert conferir_mod.noites_fecham(_viagem_base()) == []


def test_noites_que_nao_fecham_acusam():
    v = _viagem_base()
    v["roteiro"][1]["noites"] = 5
    achados = conferir_mod.noites_fecham(v)
    assert achados and "5" in str(achados[0]) and "9" in str(achados[0])


def test_trecho_em_data_bloqueada_acusa():
    v = _viagem_base(datas_bloqueadas=[
        {"data": "2027-03-10", "razao": "feriado", "decisao": "evitar o feriado"}])
    achados = conferir_mod.roteiro_respeita_bloqueios(v)
    assert any("2027-03-10" in str(a) for a in achados)


def test_trecho_fora_de_data_bloqueada_fica_calado():
    v = _viagem_base(datas_bloqueadas=[
        {"data": "2027-03-14", "razao": "feriado", "decisao": "evitar o feriado"}])
    assert conferir_mod.roteiro_respeita_bloqueios(v) == []


def test_decisao_que_trava_dia_sem_dado_acusa():
    v = _viagem_base(decisoes=["Passeio movido de 12/03: feriado local lota tudo."])
    achados = conferir_mod.decisao_virou_dado(v)
    assert achados and "2027-03-12" in str(achados[0])


def test_decisao_com_data_mas_sem_vocabulario_de_bloqueio_fica_calada():
    """O vies e o silencio: decisao cita data por muitos motivos que nao travam
    dia nenhum. Alarme em toda decisao com data seria descartado na primeira
    semana, e ai o alarme util morre junto."""
    v = _viagem_base(decisoes=["Cotacao de passagem levantada em 12/03."])
    assert conferir_mod.decisao_virou_dado(v) == []


def test_decisao_ja_convertida_em_dado_fica_calada():
    v = _viagem_base(
        decisoes=["Passeio movido de 12/03: feriado local lota tudo."],
        datas_bloqueadas=[{"data": "2027-03-12", "razao": "feriado",
                           "decisao": "Passeio movido de 12/03"}])
    assert conferir_mod.decisao_virou_dado(v) == []


def test_faixa_declarada_que_bate_fica_calada():
    v = _viagem_base(orcamento={"ponto_de_ruptura": "entre R$ 1.000 a 1.000"})
    assert not [a for a in conferir_mod.orcamento_fecha(v)
                if "ponto_de_ruptura" in a.campo]


def test_faixa_declarada_que_nao_bate_acusa():
    v = _viagem_base(orcamento={"ponto_de_ruptura": "de R$ 300 a 400"})
    achados = [a for a in conferir_mod.orcamento_fecha(v) if "ponto_de_ruptura" in a.campo]
    assert achados and "1,000" in str(achados[0])


def test_estimativa_por_diaria_multiplica_pelas_noites():
    """Estimativa de diaria somada como total sai 9x menor e calada - foi assim
    que a faixa da viagem real saiu R$ 8 mil abaixo do que as linhas sustentam."""
    v = _viagem_base()
    v["custos"].append({"item": "Hospedagem", "valor": None, "moeda": "BRL",
                        "por_pessoa": False, "noites": 9,
                        "estimativa": "R$ 100 a 200 a diaria"})
    lo, hi, _ = conferir_mod.faixa_do_orcamento(v)
    assert (lo, hi) == (1000 + 900, 1000 + 1800)


def test_valor_solto_fora_de_custos_acusa():
    v = _viagem_base(orcamento={"linhas_brl": {"passeios": 500}})
    assert any("linhas_brl" in a.campo for a in conferir_mod.orcamento_fecha(v))


def test_bater_com_uma_hipotese_de_pouso_nao_cala_a_contagem():
    """Com a passagem sem preco, o pouso admite duas datas. Declarar o numero de
    uma delas nao fecha a conta: e escolher um palpite, e o requisito proibe
    eleger. Foi o caso real - 17 noites declaradas, 17 ou 18 possiveis, e a
    hospedagem dimensionada numa hipotese que ninguem confirmou."""
    v = _viagem_base()
    v["custos"].append({"item": "Passagem", "valor": None, "moeda": "BRL",
                        "por_pessoa": True, "estimativa": "R$ 1.000 a 2.000"})
    achados = conferir_mod.noites_fecham(v)
    assert achados, "calou porque o palpite casou com uma das hipoteses"
    assert "8" in str(achados[0]) and "9" in str(achados[0])


# --- sobretaxa do destino ---------------------------------------------------
# A sobretaxa do Alipay e do destino: entra no gasto em yuan, nao no eSIM comprado
# em dolar no Brasil. Nenhum destes toca a rede - a cotacao entra pelo arquivo, ou
# o `cotar` do consolidar e trocado por uma cotacao fixa.

cambio_mod = carregar(SKILLS / "cambio-br" / "scripts" / "cambio.py")


def _viagem_china():
    """Mesmo valor em yuan e em dolar, com cotacao 1 e spread 0: a diferenca entre
    as duas linhas e exatamente a sobretaxa, e ela so pode estar na de yuan."""
    v = _viagem_base()
    v["destino"] = {"cidade": "Cidade A", "pais": "CN"}
    v["moeda_local"] = "CNY"
    v["orcamento"] = {"cotacoes": {"CNY": 1.0, "USD": 1.0}}
    v["custos"] = [
        {"item": "Gasto em yuan", "valor": 1000, "moeda": "CNY", "por_pessoa": False,
         "consultado_em": "2027-01-01"},
        {"item": "eSIM em dolar", "valor": 1000, "moeda": "USD", "por_pessoa": False,
         "consultado_em": "2027-01-01"},
    ]
    return v


def _consolidar_sem_rede(tmp_path, monkeypatch, capsys, v):
    arq = tmp_path / "viagem.json"
    arq.write_text(json.dumps(v), encoding="utf-8")
    monkeypatch.setattr(consolidar, "cotar", lambda cb, moeda: (1.0, "teste", None))
    return _rodar(str(arq), monkeypatch, capsys)


def test_sobretaxa_do_destino_acha_a_china_e_nao_acha_portugal():
    achada = cambio_mod.sobretaxa_do_destino("CN")
    assert achada is not None and achada[0] == pytest.approx(0.03)
    assert achada[1].endswith("china-cuidados.json")
    assert cambio_mod.sobretaxa_do_destino("PT") is None


def test_faixa_do_conferidor_poe_sobretaxa_so_na_moeda_local():
    iof = cambio_mod.iof()["aliquotas"]["cartao_credito_internacional"]["valor"]
    lo, hi, _ = conferir_mod.faixa_do_orcamento(_viagem_china())
    assert lo == hi == pytest.approx(1000 * (1 + iof) * 1.03 + 1000 * (1 + iof))


def test_consolidador_mostra_a_sobretaxa_so_na_linha_em_moeda_local(tmp_path, monkeypatch, capsys):
    """A carga por componente e o que deixa ver que a sobretaxa entrou no yuan e
    nao no dolar. Um percentual unico esconderia exatamente isso."""
    linhas = _consolidar_sem_rede(tmp_path, monkeypatch, capsys, _viagem_china()).splitlines()
    yuan = next(i for i, l in enumerate(linhas) if l.startswith("Gasto em yuan"))
    dolar = next(i for i, l in enumerate(linhas) if l.startswith("eSIM em dolar"))
    assert "sobretaxa 3.0%" in linhas[yuan + 1]
    assert "carga" in linhas[dolar + 1] and "sobretaxa" not in linhas[dolar + 1]


def test_consolidador_avisa_antes_da_tabela_que_a_isencao_nao_alcanca(tmp_path, monkeypatch, capsys):
    """A isencao abaixo de CNY 200 vale ate 31/12/2026, e a viagem e em 2027. O
    aviso vem antes dos numeros: contexto antes da conta."""
    saida = _consolidar_sem_rede(tmp_path, monkeypatch, capsys, _viagem_china())
    assert "nao alcanca esta viagem" in saida
    assert saida.index("nao alcanca") < saida.index("Item")
    assert "sobretaxa 3.0% em CNY" in saida


def test_portugal_nao_ganha_sobretaxa(tmp_path, monkeypatch, capsys):
    """Nao fixa total absoluto - ele se move com a cotacao. Fixa so a ausencia."""
    saida = _rodar(_viagem(tmp_path, [
        {"item": "Hotel", "valor": 1000, "moeda": "BRL", "por_pessoa": False,
         "consultado_em": date.today().isoformat()}]), monkeypatch, capsys)
    assert "sobretaxa" not in saida


def test_sobretaxa_com_linha_na_moeda_local_nao_acusa():
    """Depois da Fase 4 o consolidar aplica a sobretaxa sozinho. Acusar 'fora do
    orcamento' seria alarme permanente sobre algo que ja esta no total."""
    assert conferir_mod.sobretaxa_chegou_no_orcamento(_viagem_china()) == []


def test_sobretaxa_sem_linha_na_moeda_local_acusa_nomeando_o_arquivo():
    v = _viagem_china()
    v["custos"] = [c for c in v["custos"] if c["moeda"] != "CNY"]
    achados = conferir_mod.sobretaxa_chegou_no_orcamento(v)
    assert achados and "CNY" in str(achados[0])
    assert "china-cuidados.json" in achados[0].campo


# --- cobertura criterio a criterio -----------------------------------------
# O que as fases anteriores so verificaram rodando contra o arquivo real. Rodar a
# mao prova que funcionou naquele dia; so teste impede de voltar a quebrar.

def _hospedagem(**campos):
    return {"item": "Hospedagem", "valor": 900, "moeda": "BRL", "por_pessoa": False,
            "consultado_em": "2027-01-01", **campos}


def test_hospedagem_que_orca_noites_diferentes_do_roteiro_acusa():
    v = _viagem_base()
    v["custos"].append(_hospedagem(noites=5))
    achados = conferir_mod.hospedagem_bate_com_o_roteiro(v)
    assert achados and "5" in str(achados[0]) and "9" in str(achados[0])


def test_hospedagem_com_as_mesmas_noites_do_roteiro_fica_calada():
    v = _viagem_base()
    v["custos"].append(_hospedagem(noites=9))
    assert conferir_mod.hospedagem_bate_com_o_roteiro(v) == []


def test_hospedagem_sem_noites_declara_que_nao_pode_ser_conferida():
    v = _viagem_base()
    v["custos"].append(_hospedagem())
    achados = conferir_mod.hospedagem_bate_com_o_roteiro(v)
    assert achados and "nao da para conferir" in str(achados[0])


def test_trecho_em_data_bloqueada_nomeia_o_trecho_e_a_decisao():
    v = _viagem_base(datas_bloqueadas=[
        {"data": "2027-03-10", "razao": "feriado", "decisao": "evitar o feriado local"}])
    d = [a for a in conferir_mod.roteiro_respeita_bloqueios(v) if "A -> B" in a.campo]
    assert d and "evitar o feriado local" in d[0].correcao


def test_data_bloqueada_sem_decisao_vira_bloqueio_sem_procedencia():
    v = _viagem_base(datas_bloqueadas=[{"data": "2027-03-14", "razao": "feriado"}])
    achados = conferir_mod.roteiro_respeita_bloqueios(v)
    assert any("sem dizer qual decisao" in str(a) for a in achados)


def test_duas_cidades_no_mesmo_dia_sem_trecho_acusa():
    v = _viagem_base()
    v["roteiro"].append({"cidade": "C", "dias": "10", "noites": 0})
    achados = conferir_mod.roteiro_respeita_bloqueios(v)
    assert any("(B x C)" in str(a) for a in achados)


def test_duas_cidades_no_dia_de_um_trecho_ficam_caladas():
    """Sair de uma e chegar na outra no mesmo dia e o normal de um dia de viagem."""
    v = _viagem_base()
    v["roteiro"] += [{"trecho": "B -> C", "dias": "10"},
                     {"cidade": "C", "dias": "10", "noites": 0}]
    assert conferir_mod.roteiro_respeita_bloqueios(v) == []


def test_folga_entra_na_faixa_calculada():
    v = _viagem_base()
    v["custos"].append({"item": "Folga para imprevisto", "valor": 500, "moeda": "BRL",
                        "por_pessoa": False, "consultado_em": "2027-01-01"})
    lo, hi, _ = conferir_mod.faixa_do_orcamento(v)
    assert (lo, hi) == (1500, 1500)


def test_piso_acima_do_orcamento_informado_registra_o_estouro():
    v = _viagem_base(orcamento={"informado_brl": 800})
    achados = [a for a in conferir_mod.orcamento_fecha(v) if "informado" in a.campo]
    assert achados and "200" in achados[0].correcao


def test_piso_dentro_do_orcamento_informado_fica_calado():
    v = _viagem_base(orcamento={"informado_brl": 5000})
    assert not [a for a in conferir_mod.orcamento_fecha(v) if "informado" in a.campo]


def test_linha_sem_estimativa_deixa_a_faixa_incompleta_sem_derruba_la():
    v = _viagem_base()
    v["custos"].append({"item": "Passagem", "valor": None, "moeda": "BRL", "por_pessoa": True})
    lo, hi, fora = conferir_mod.faixa_do_orcamento(v)
    assert (lo, hi) == (1000, 1000), "a recusa de uma linha derrubou as outras"
    assert fora == [("Passagem", "sem estimativa: a faixa calculada esta incompleta")]


def test_estimativa_sem_minimo_e_maximo_nao_entra_na_faixa():
    v = _viagem_base()
    v["custos"].append({"item": "Passagem", "valor": None, "moeda": "BRL",
                        "por_pessoa": True, "estimativa": "uns 8 mil"})
    lo, hi, fora = conferir_mod.faixa_do_orcamento(v)
    assert (lo, hi) == (1000, 1000)
    assert fora == [("Passagem", "estimativa sem minimo e maximo: nao entra na faixa")]


def test_conferidor_acusa_custos_vazio():
    v = _viagem_base()
    v["custos"] = []
    achados = conferir_mod.orcamento_fecha(v)
    assert achados and "nao tem custo algum" in str(achados[0])


def _com_ingresso(**campos):
    """Visita a B no dia 2 da viagem, 11/03/2027, uma quinta. Janela de 7 dias."""
    return _viagem_base(itens_com_prazo=[
        {"item": "Ingresso", "janela_dias": 7, "cidade": "B", "critico": True, **campos}])


def test_data_de_compra_sai_da_visita_menos_a_janela():
    v = _com_ingresso()
    assert conferir_mod.data_de_compra(v, v["itens_com_prazo"][0]) == date(2027, 3, 4)


def test_data_de_compra_fixada_diferente_da_derivada_acusa():
    achados = conferir_mod.janela_de_compra_fecha(_com_ingresso(data_compra="2027-03-05"))
    assert achados and "2027-03-05" in str(achados[0]) and "2027-03-04" in str(achados[0])


def test_data_de_compra_fixada_igual_a_derivada_fica_calada():
    assert conferir_mod.janela_de_compra_fecha(_com_ingresso(data_compra="2027-03-04")) == []


def test_visita_em_dia_restrito_do_proprio_item_acusa():
    achados = conferir_mod.janela_de_compra_fecha(_com_ingresso(dias_restritos=["quinta"]))
    assert achados and "quinta" in str(achados[0])


def test_item_critico_sem_data_de_visita_acusa():
    achados = conferir_mod.janela_de_compra_fecha(_com_ingresso(cidade="Nenhuma"))
    assert achados and "nao pode ser derivada" in str(achados[0])


def test_arquivo_que_nao_existe_falha_dizendo_isso(tmp_path, monkeypatch, capsys):
    pasta, _ = _viagem_minima(tmp_path)
    assert _rodar_conferidor(monkeypatch, pasta,
                             ["conferir.py", str(tmp_path / "sumiu.json")]) != 0
    assert "nao existe" in capsys.readouterr().err


def test_correcao_sugerida_sai_como_texto_e_o_arquivo_fica_igual(tmp_path, monkeypatch, capsys):
    """O conferidor sabe a correcao e mesmo assim nao a aplica: reescrever apagaria a
    razao registrada na decisao. Ela vai para o relatorio, e so para ele."""
    pasta, arq = _viagem_minima(tmp_path)
    antes = arq.read_bytes()
    d = conferir_mod.Divergencia("calendario", "roteiro[0].noites", "nao fecha", (5, 9))
    d.correcao = "acertar as noites do roteiro para 9"
    monkeypatch.setattr(conferir_mod, "FAMILIAS", [lambda v: [d]])
    _rodar_conferidor(monkeypatch, pasta, ["conferir.py"])
    saida = capsys.readouterr()
    assert "correcao sugerida: acertar as noites do roteiro para 9" in saida.out
    assert saida.err == "", "relatorio escapou da saida padrao"
    assert arq.read_bytes() == antes
    assert sorted(p.name for p in pasta.iterdir()) == ["v.json"], "o conferidor criou arquivo"
