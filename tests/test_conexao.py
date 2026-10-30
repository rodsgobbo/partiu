"""Testes da checagem de documento de conexao no `conferir.py`.

Os dois primeiros usam os arquivos reais de `dados/`: sao o criterio de pronto do
item 5.4 do backlog. O resto injeta dados, para o teste falhar por bug e nunca
porque alguem atualizou uma regra de transito.
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def carregar(caminho: Path):
    spec = importlib.util.spec_from_file_location(caminho.stem, caminho)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


conferir = carregar(RAIZ / "conferir.py")

DADOS = ({"ORD": "US", "LIS": "PT", "LHR": "GB", "XXX": "ZZ", "PEK": "CN"},
         {"US": {"airside": {"exige_um_de": ["visto:US"]},
                 "conta_propria": {"exige_um_de": ["visto:US"]}, "nota": "sem TWOV"},
          "GB": {"airside": {"livre": True},
                 "conta_propria": {"exige_um_de": ["eta:GB"]}, "nota": "temporario"}},
         {"US": "visa required", "PT": "90", "GB": "eta", "ZZ": "visa required",
          "CN": "30"})


def viagem(conexoes, tem=None, destino="CN", **linha):
    return {"destino": {"pais": destino},
            "documentos": {"tem": tem or []},
            "custos": [{"item": "Passagem", "valor": 5000, "moeda": "BRL",
                        "por_pessoa": True, "conexoes": conexoes, **linha}]}


def acusa(v):
    return conferir.conexoes_tem_documento(v, DADOS)


# --- criterio de pronto, com os dados reais ---------------------------------


def rodar(tmp_path, v):
    """Com os dados reais de dados/, sem injecao."""
    return conferir.conexoes_tem_documento(v)


def test_conexao_em_chicago_sem_visto_americano_e_acusada(tmp_path):
    achados = rodar(tmp_path, viagem(["ORD"]))
    assert len(achados) == 1
    assert "ORD" in achados[0].campo, "o relatorio tem de citar o trecho"


def test_conexao_em_lisboa_passa(tmp_path):
    assert rodar(tmp_path, viagem(["LIS"])) == []


def test_conferir_sai_1_no_arquivo_com_conexao_em_chicago(tmp_path):
    arq = tmp_path / "v.json"
    v = viagem(["ORD"])
    v.update({"datas": {"ida": "2027-03-10", "volta": "2027-03-20"}})
    arq.write_text(json.dumps(v), encoding="utf-8")
    r = subprocess.run([sys.executable, str(RAIZ / "conferir.py"), str(arq)],
                       capture_output=True, text=True)
    assert r.returncode == 1
    assert "ORD" in r.stdout


# --- as regras ---------------------------------------------------------------


def test_visto_declarado_libera_a_conexao():
    assert acusa(viagem(["ORD"], tem=["visto:US"])) == []


def test_conexao_airside_no_reino_unido_passa_sem_eta():
    assert acusa(viagem(["LHR"])) == []


def test_bilhete_separado_no_reino_unido_exige_eta():
    """Despachar a mala de novo e passar pela imigracao: vale a regra de entrada."""
    assert len(acusa(viagem(["LHR"], por_conta_propria=True))) == 1


def test_por_conta_propria_vale_por_conexao_tambem():
    v = viagem([{"aeroporto": "LHR", "por_conta_propria": True}])
    assert len(acusa(v)) == 1


def test_aeroporto_desconhecido_nao_passa_calado():
    achados = acusa(viagem(["QQQ"]))
    assert "sem pais" in achados[0].mensagem


def test_pais_sem_regra_de_transito_e_entrada_com_visto_e_acusado():
    """Nunca liberar no escuro: sem regra apurada, a entrada com visto acusa."""
    achados = acusa(viagem(["XXX"]))
    assert "nao apurada" in achados[0].mensagem


def test_pais_sem_regra_de_transito_e_entrada_livre_passa():
    assert acusa(viagem(["LIS"])) == []


def test_conexao_no_proprio_destino_e_assunto_da_documentos_br():
    assert acusa(viagem(["PEK"], destino="CN")) == []


def test_viagem_sem_conexoes_declaradas_nao_e_conferida_nem_quebra():
    v = {"destino": {"pais": "PT"}, "custos": [{"item": "x", "valor": 1}]}
    assert conferir.conexoes_tem_documento(v) == []


# --- os arquivos reais ----------------------------------------------------------


def test_todo_pais_com_regra_de_transito_tem_fonte_e_reconferencia():
    d = json.loads((RAIZ / "dados" / "transito.json").read_text(encoding="utf-8"))
    for pais, r in d["por_pais"].items():
        assert r.get("fonte"), pais
        assert r.get("reconferir_em"), f"{pais}: regra de transito estraga"
        assert "airside" in r and "conta_propria" in r, pais


# --- 5.5: bilhete separado e cidade oculta ----------------------------------


def risco(**linha):
    v = {"custos": [{"item": "Passagem", "valor": 1, **linha}]}
    return conferir.bilhete_separado_declara_o_risco(v)


def test_bilhete_separado_sem_margem_e_acusado():
    assert len(risco(por_conta_propria=True)) == 1


def test_margem_sem_fonte_nao_conta():
    """Numero sem fonte e lembranca, nao margem."""
    assert len(risco(por_conta_propria=True, margem_conexao={"minutos": 240})) == 1


def test_margem_com_fonte_passa():
    assert risco(por_conta_propria=True,
                 margem_conexao={"minutos": 240, "minima": 180, "fonte": "aeroporto"}) == []


def test_margem_abaixo_da_minima_e_acusada():
    achados = risco(por_conta_propria=True,
                    margem_conexao={"minutos": 90, "minima": 180, "fonte": "aeroporto"})
    assert "abaixo da minima" in achados[0].mensagem


def test_por_conta_propria_numa_conexao_so_tambem_pede_margem():
    assert len(risco(conexoes=[{"aeroporto": "LHR", "por_conta_propria": True}])) == 1


def test_cidade_oculta_sem_declarar_bagagem_e_acusada():
    """Silencio aqui e a mala indo para o destino final do bilhete."""
    assert len(risco(cidade_oculta=True)) == 1


def test_cidade_oculta_so_com_mala_de_mao_passa():
    assert risco(cidade_oculta=True, bagagem_despachada=False) == []


def test_voo_comum_nao_pede_nada():
    assert risco(conexoes=["LIS"]) == []
