"""Testes da taxa turistica no `consolidar.py`. Os dados entram como parametro,
para o teste falhar por bug e nunca porque alguem atualizou uma aliquota em
`dados/taxa-turistica.json`. So o ultimo bloco le o arquivo real, e so para
conferir a forma.
"""
import importlib.util
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def carregar(caminho: Path):
    spec = importlib.util.spec_from_file_location(caminho.stem, caminho)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


consolidar = carregar(RAIZ / ".claude" / "skills" / "viagem" / "scripts" / "consolidar.py")

POR_NOITE = {"nome": "Taxa da cidade", "tipo": "por_noite_pessoa",
             "consultado_em": "2026-10-30",
             "vigencias": [{"de": "2024-09-01", "ate": None, "valor": 4.0, "moeda": "EUR",
                            "max_noites": 7, "status": "em_vigor", "verificado": True}]}
PERCENTUAL = {"nome": "Imposto de hospedagem", "tipo": "percentual_diaria",
              "consultado_em": "2026-10-30",
              "vigencias": [{"de": "2026-05-01", "ate": "2026-12-31", "valor": 0.01,
                             "status": "em_vigor"},
                            {"de": "2027-01-01", "ate": None, "valor": 0.02,
                             "status": "em_vigor"}]}
ENTRADA = {"nome": "Taxa de entrada", "tipo": "entrada", "reconferir_em": "2027-01-31",
           "vigencias": [{"de": None, "ate": None, "valor": None, "moeda": "THB",
                          "faixa_proposta": [300, 450], "status": "proposta"}]}
DADOS = {"por_pais": {"PT": {"cidades": {"Lisboa": POR_NOITE}},
                      "TR": {"nacional": PERCENTUAL},
                      "TH": {"nacional": ENTRADA}}}


def viagem(pais, cidade, custos, ida="2027-03-10"):
    return {"destino": {"pais": pais, "cidade": cidade}, "datas": {"ida": ida},
            "custos": custos}


def hospedagem(**extra):
    return {"item": "Hotel", "valor": 1000.0, "moeda": "EUR", "por_pessoa": False,
            "noites": 9, **extra}


def test_hospedagem_sem_declaracao_ganha_a_taxa_estimada_e_o_aviso():
    """O ponto do item 5.2: preco de vitrine nao e o preco."""
    linhas, avisos = consolidar.taxas_turisticas(
        viagem("PT", "Lisboa", [hospedagem()]), DADOS, 2)
    assert len(linhas) == 1 and len(avisos) == 1
    assert "taxa_turistica" in avisos[0], "o aviso tem de dizer como silenciar"


def test_por_noite_respeita_o_teto_de_noites():
    """9 noites, teto 7: cobrar 9 inflaria o total com taxa que ninguem cobra."""
    linhas, _ = consolidar.taxas_turisticas(viagem("PT", "Lisboa", [hospedagem()]), DADOS, 2)
    assert linhas[0]["valor"] == 4.0 * 7 * 2


def test_declarada_inclusa_nao_conta_duas_vezes():
    linhas, avisos = consolidar.taxas_turisticas(
        viagem("PT", "Lisboa", [hospedagem(taxa_turistica="inclusa")]), DADOS, 2)
    assert linhas == [] and avisos == []


def test_declarada_separada_nao_conta_duas_vezes():
    linhas, _ = consolidar.taxas_turisticas(
        viagem("PT", "Lisboa", [hospedagem(taxa_turistica="separada")]), DADOS, 2)
    assert linhas == []


def test_linha_sem_noites_nao_e_hospedagem():
    passeio = {"item": "Passeios", "valor": 700.0, "moeda": "EUR", "por_pessoa": True}
    linhas, _ = consolidar.taxas_turisticas(viagem("PT", "Lisboa", [passeio]), DADOS, 2)
    assert linhas == []


def test_cidade_sem_regra_nao_inventa_taxa():
    linhas, _ = consolidar.taxas_turisticas(viagem("PT", "Porto", [hospedagem()]), DADOS, 2)
    assert linhas == []


def test_cidade_da_linha_vence_a_do_destino():
    """Viagem por varias cidades: a taxa e de onde se dorme, nao do destino."""
    linhas, _ = consolidar.taxas_turisticas(
        viagem("PT", "Porto", [hospedagem(cidade="Lisboa")]), DADOS, 1)
    assert len(linhas) == 1


def test_percentual_escolhe_a_vigencia_pela_data_da_ida():
    """A Turquia muda de 1% para 2% na virada de 2027. Aplicar a aliquota de hoje
    numa viagem de 2027 corta a taxa pela metade, calado."""
    linhas, _ = consolidar.taxas_turisticas(
        viagem("TR", "Istambul", [hospedagem()], ida="2027-08-15"), DADOS, 2)
    assert linhas[0]["valor"] == 20.0
    linhas, _ = consolidar.taxas_turisticas(
        viagem("TR", "Istambul", [hospedagem()], ida="2026-11-10"), DADOS, 2)
    assert linhas[0]["valor"] == 10.0


def test_percentual_sobre_hospedagem_sem_preco_avisa_em_vez_de_sumir():
    """Era o caso real da Turquia: sem base, a taxa sumia calada do relatorio."""
    linhas, avisos = consolidar.taxas_turisticas(
        viagem("TR", "Istambul", [hospedagem(valor=None)], ida="2027-08-15"), DADOS, 2)
    assert linhas == []
    assert any("2%" in a for a in avisos)


def test_taxa_proposta_avisa_e_fica_fora_do_total():
    """Proposta nao e lei. Somar seria inventar custo; calar seria esconder risco."""
    linhas, avisos = consolidar.taxas_turisticas(viagem("TH", "Bangkok", []), DADOS, 2)
    assert linhas == []
    assert any("proposta" in a for a in avisos)


def test_aliquota_nao_verificada_se_denuncia():
    dados = json.loads(json.dumps(DADOS))
    dados["por_pais"]["PT"]["cidades"]["Lisboa"]["vigencias"][0]["verificado"] = False
    _, avisos = consolidar.taxas_turisticas(viagem("PT", "Lisboa", [hospedagem()]), dados, 2)
    assert "NAO VERIFICADA" in avisos[0]


# --- o arquivo real -----------------------------------------------------------


def test_arquivo_real_tem_vigencia_valida_por_regra():
    d = consolidar.carregar_taxas()
    regras = []
    for pais in d["por_pais"].values():
        regras += list((pais.get("cidades") or {}).values())
        if pais.get("nacional"):
            regras.append(pais["nacional"])
    assert len(regras) >= 3, "o item 5.2 pede 3 destinos"
    for r in regras:
        assert r["tipo"] in d["tipos"], r["nome"]
        assert r.get("reconferir_em"), f"{r['nome']} sem reconferir_em: taxa estraga"
        for vig in r["vigencias"]:
            assert vig.get("fonte"), f"{r['nome']}: vigencia sem fonte"


# --- 5.8: onde o dinheiro esta ------------------------------------------------


def test_maiores_linhas_em_ordem_e_com_a_fatia():
    linhas = [("Bagagem", 100.0, "EUR"), ("Passagem", 8000.0, "BRL"),
              ("Hotel", 1900.0, "EUR"), ("eSIM", 0.0, "USD")]
    m = consolidar.maiores_linhas(linhas, 10000.0)
    assert [x[0] for x in m] == ["Passagem", "Hotel", "Bagagem"]
    assert m[0][2] == 0.8


def test_maiores_linhas_com_total_zero_nao_divide():
    assert consolidar.maiores_linhas([], 0.0) == []
