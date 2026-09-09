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
    """A conta canonica mora no cambio.py. Se o consolidar voltar a ter a sua
    propria copia, os dois divergem no primeiro ajuste de aliquota."""
    cambio = carregar(SKILLS / "cambio-br" / "scripts" / "cambio.py")
    assert cambio.em_reais(100.0, 6.0, 0.04, 0.035) == pytest.approx(100 * 6 * 1.04 * 1.035)
    fonte = (SKILLS / "viagem" / "scripts" / "consolidar.py").read_text(encoding="utf-8")
    assert "cb.em_reais(" in fonte, "consolidar deixou de usar a formula canonica"
    assert "(1 + spread) * (1 + taxa_iof)" not in fonte, "copia da formula voltou"


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
