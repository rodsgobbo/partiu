"""Testes do `veredito.py`. A data de hoje entra como parametro e os prazos
genericos tambem, para o teste falhar por bug e nunca por o tempo ter passado ou
por alguem apurar um prazo em `dados/prazos.json`.
"""
import importlib.util
import sys
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))        # o veredito importa o recotar pelo nome


def carregar(caminho: Path):
    spec = importlib.util.spec_from_file_location(caminho.stem, caminho)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


veredito = carregar(RAIZ / "veredito.py")
HOJE = date(2026, 10, 30)
IDA = "2027-03-10"                   # 131 dias: janela aberta
PRAZOS = {"visto": {"prazo_dias": None}, "civp": {"prazo_dias": 10},
          "eta": {"prazo_dias": None}}


def tendencia(direcao="estavel", dias_atras=0, **extra):
    return {"direcao": direcao, "fonte": "trvl watch history",
            "consultado_em": (HOJE - timedelta(days=dias_atras)).isoformat(), **extra}


def passagem(valor=4000, dias_atras=0, tend=None, **extra):
    c = {"item": "Passagem", "valor": valor, "moeda": "BRL", "por_pessoa": True,
         "volatilidade": "alta", "depende_da_janela_aerea": True, **extra}
    if valor is not None:
        c["consultado_em"] = (HOJE - timedelta(days=dias_atras)).isoformat()
    if tend is not None:
        c["tendencia"] = tend
    return c


def viagem(c, ida=IDA, volta="2027-03-20", exige=(), prazos=None):
    docs = {} if exige is None else {"exige": list(exige)}
    if prazos:
        docs["prazos"] = prazos
    return {"datas": {"ida": ida, "volta": volta}, "documentos": docs, "custos": [c]}


def decidir(v):
    return veredito.decidir(v, v["custos"][0], HOJE, PRAZOS)


# --- a regra que governa: documento vence tendencia ---------------------------


def test_tendencia_caindo_com_documento_apertado_manda_reservar():
    """O ponto inteiro do item 5.1. Esperar uma queda que chega depois do limite
    do visto nao e economia."""
    v = viagem(passagem(tend=tendencia("caindo")), exige=["visto"],
               prazos={"visto": {"dias": 125, "fonte": "consulado"}})   # limite em 6d
    d = decidir(v)
    assert d["veredito"] == "RESERVE"
    assert d["decidiu"] == "documento", "quem decidiu tem de ser nomeado"


def test_tendencia_caindo_com_folga_espera_e_diz_ate_quando():
    v = viagem(passagem(tend=tendencia("caindo")), exige=["visto"],
               prazos={"visto": {"dias": 30, "fonte": "consulado"}})
    d = decidir(v)
    assert d["veredito"] == "ESPERE"
    limite = date(2027, 3, 10) - timedelta(days=30)
    assert d["ate"] == limite - timedelta(days=veredito.MARGEM_DIAS), \
        "espera sem data final e esquecimento com outro nome"


def test_documento_vencido_muda_o_plano_mesmo_sem_tendencia():
    """Nenhum preco salva viagem em que nao se embarca - e por isso o documento
    vencido decide antes de olhar se falta insumo."""
    v = viagem(passagem(), exige=["visto"],
               prazos={"visto": {"dias": 200, "fonte": "consulado"}})
    assert decidir(v)["veredito"] == "MUDE"


def test_venda_que_abre_depois_do_limite_do_documento_muda_o_plano():
    # venda abre ~2026-12-24; o visto, a 380d da ida, fecha em 2026-11-25
    v = viagem(passagem(valor=None), ida="2027-12-10", volta="2027-12-20",
               exige=["visto"], prazos={"visto": {"dias": 380, "fonte": "consulado"}})
    d = decidir(v)
    assert d["veredito"] == "MUDE"
    assert "venda abre" in d["motivo"]


def test_prazo_da_viagem_vence_o_generico():
    """O generico de visto e null; o apurado no consulado e o que vale."""
    v = viagem(passagem(tend=tendencia("subindo")), exige=["visto"],
               prazos={"visto": {"dias": 30, "fonte": "consulado"}})
    assert decidir(v)["veredito"] == "RESERVE"


# --- insumo faltando: dizer, nao decidir ------------------------------------


def test_sem_documentos_exige_nao_ha_veredito():
    """Campo ausente nao e "nada a providenciar": e a documentos-br que nao rodou."""
    v = viagem(passagem(tend=tendencia("subindo")), exige=None)
    d = decidir(v)
    assert d["veredito"] == "SEM VEREDITO"
    assert any("documentos.exige" in f for f in d["faltando"])


def test_exige_vazio_e_resposta_e_nao_limita():
    v = viagem(passagem(tend=tendencia("subindo")), exige=[])
    assert decidir(v)["veredito"] == "RESERVE"


def test_prazo_nao_apurado_nao_vira_zero():
    """Visto exigido sem prazo apurado: inventar um numero seria pior que parar."""
    v = viagem(passagem(tend=tendencia("subindo")), exige=["visto"])
    d = decidir(v)
    assert d["veredito"] == "SEM VEREDITO"
    assert any("visto" in f for f in d["faltando"])


def test_prazo_nao_verificado_decide_mas_se_denuncia():
    """Teto sobre fonte secundaria serve para decidir; calado, viraria dado."""
    v = viagem(passagem(tend=tendencia("caindo")), exige=["visto"],
               prazos={"visto": {"dias": 125, "fonte": "agencias", "verificado": False}})
    d = decidir(v)
    assert d["decidiu"] == "documento"
    assert "NAO VERIFICADO" in d["motivo"]


def test_prazo_generico_apurado_basta():
    v = viagem(passagem(tend=tendencia("subindo")), exige=["civp"])
    assert decidir(v)["veredito"] == "RESERVE"


def test_sem_tendencia_nao_ha_veredito():
    d = decidir(viagem(passagem()))
    assert d["veredito"] == "SEM VEREDITO"
    assert any("watch history" in f for f in d["faltando"])


def test_tendencia_velha_nao_conta():
    d = decidir(viagem(passagem(tend=tendencia("subindo", dias_atras=30))))
    assert d["veredito"] == "SEM VEREDITO"


def test_cotacao_velha_nao_conta():
    """Reservar em cima de preco de um mes atras e reservar outro preco."""
    d = decidir(viagem(passagem(dias_atras=30, tend=tendencia("subindo"))))
    assert d["veredito"] == "SEM VEREDITO"
    assert any("recote" in f for f in d["faltando"])


def test_todos_os_insumos_faltando_aparecem_juntos():
    """Um por vez obrigaria tres rodadas para descobrir o que ja se sabia."""
    v = viagem(passagem(dias_atras=30), exige=None)
    assert len(decidir(v)["faltando"]) == 3


# --- janela aerea -------------------------------------------------------------


def test_bilhete_fora_da_venda_espera_ate_a_abertura():
    v = viagem(passagem(valor=None), ida="2027-12-10", volta="2027-12-20")
    d = decidir(v)
    assert d["veredito"] == "ESPERE"
    assert d["decidiu"] == "janela aerea"
    assert d["ate"] == date(2027, 12, 20) - timedelta(days=veredito.recotar.JANELA_AEREA_DIAS)


# --- faixa historica ----------------------------------------------------------


def test_estavel_acima_da_faixa_espera():
    t = tendencia("estavel", faixa={"min": 3000, "max": 3800, "moeda": "BRL"})
    assert decidir(viagem(passagem(tend=t)))["veredito"] == "ESPERE"


def test_estavel_dentro_da_faixa_reserva():
    t = tendencia("estavel", faixa={"min": 3000, "max": 4500, "moeda": "BRL"})
    assert decidir(viagem(passagem(tend=t)))["veredito"] == "RESERVE"


def test_faixa_em_outra_moeda_nao_e_comparada():
    """Sem conversao aqui: comparar BRL com EUR cru diria "barato" para tudo."""
    t = tendencia("estavel", faixa={"min": 500, "max": 700, "moeda": "EUR"})
    d = decidir(viagem(passagem(tend=t)))
    assert d["veredito"] == "RESERVE"
    assert "sem faixa" in d["motivo"]


# --- os arquivos publicos do repo --------------------------------------------


def test_exemplo_publico_decide_com_os_prazos_reais():
    """O exemplo de Lisboa declara tudo que o veredito le: tem de sair com um."""
    import json
    v = json.loads((RAIZ / "viagens" / "exemplo-lisboa-2027-03.json").read_text(encoding="utf-8"))
    c = veredito.passagens(v)[0]
    dia = date.fromisoformat(c["consultado_em"])
    d = veredito.decidir(v, c, dia, veredito.carregar_prazos())
    assert d["veredito"] in ("RESERVE", "ESPERE"), d
