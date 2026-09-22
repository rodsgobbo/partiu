"""Testes do `recotar.py`. Nenhum toca a rede nem olha o calendario real: a data
de hoje entra como parametro, para o teste falhar por bug e nunca por o tempo ter
passado.
"""
import importlib.util
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def carregar(caminho: Path):
    spec = importlib.util.spec_from_file_location(caminho.stem, caminho)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


recotar = carregar(RAIZ / "recotar.py")
HOJE = date(2026, 9, 22)


def viagem(ida, volta, custos):
    return {"datas": {"ida": ida, "volta": volta}, "custos": custos}


def custo(item="X", valor=100, dias_atras=0, **extra):
    c = {"item": item, "valor": valor, "por_pessoa": False, **extra}
    if valor is not None:
        c["consultado_em"] = (HOJE - timedelta(days=dias_atras)).isoformat()
    return c


# --- janela de venda ---------------------------------------------------------
# Multitrecho e UM bilhete. O erro natural e olhar a ida, que e a data que a
# pessoa tem na cabeca - e foi assim que a viagem da China ficou parecendo
# cotavel por semanas, com a ida dentro da janela e a volta 11 dias fora.


def test_janela_fechada_quando_so_a_volta_esta_fora():
    v = viagem("2027-09-10", "2027-09-29", [])      # 353d e 372d
    j = recotar.janela_aerea(v, HOJE)
    assert j["aberta"] is False, "a ida dentro nao pode abrir o bilhete inteiro"


def test_janela_aberta_com_as_duas_pontas_dentro():
    v = viagem("2027-05-10", "2027-05-17", [])      # 230d e 237d
    assert recotar.janela_aerea(v, HOJE)["aberta"] is True


def test_abertura_sai_da_ponta_mais_distante():
    """A volta e a ultima a entrar a venda, entao e ela que define a data."""
    v = viagem("2027-09-10", "2027-09-29", [])
    j = recotar.janela_aerea(v, HOJE)
    assert j["abre_em"] == date(2027, 9, 29) - timedelta(days=recotar.JANELA_AEREA_DIAS)


def test_sem_datas_nao_inventa_janela():
    assert recotar.janela_aerea({"custos": []}, HOJE) is None


# --- volatilidade ------------------------------------------------------------
# O ponto inteiro do campo: uma reserva de imprevisto nao vence junto com tarifa
# aerea. Sem ele, a lista de pendencias fica sempre cheia e ninguem a le.


def test_volatilidade_baixa_nao_vence_em_21_dias():
    v = viagem("2027-05-10", "2027-05-17",
               [custo("Folga", dias_atras=25, volatilidade="baixa")])
    agora, _, revisar, _ = recotar.classificar(v, HOJE)
    assert agora == [], "reserva de imprevisto nao e tarifa"
    assert revisar == [], "25 dias esta dentro dos 180 de volatilidade baixa"


def test_volatilidade_alta_vence_em_21_dias():
    v = viagem("2027-05-10", "2027-05-17",
               [custo("Passagem", dias_atras=25, volatilidade="alta")])
    agora, _, _, _ = recotar.classificar(v, HOJE)
    assert [i for i, _ in agora] == ["Passagem"]


def test_media_vencida_vai_para_revisar_nao_para_agora():
    """Prazo medio estourado merece olhar, nao interrompe o dia - senao volta a
    ser o alarme unico que o campo veio desfazer."""
    v = viagem("2027-05-10", "2027-05-17",
               [custo("Passeios", dias_atras=70, volatilidade="media")])
    agora, _, revisar, _ = recotar.classificar(v, HOJE)
    assert agora == []
    assert [i for i, _ in revisar] == ["Passeios"]


def test_sem_volatilidade_assume_alta_e_denuncia_o_chute():
    """Assumir o pior e seguro; assumir calado nao. Quem le precisa saber que o
    prazo veio de um padrao e nao de uma declaracao."""
    v = viagem("2027-05-10", "2027-05-17", [custo("Sem campo", dias_atras=25)])
    agora, _, _, sem_vol = recotar.classificar(v, HOJE)
    assert [i for i, _ in agora] == ["Sem campo"]
    assert sem_vol == ["Sem campo"], "o chute tem de aparecer no relatorio"


# --- linhas sem preco --------------------------------------------------------


def test_passagem_fora_da_janela_aguarda_com_data_calculada():
    v = viagem("2027-09-10", "2027-09-29",
               [custo("Passagem", valor=None, depende_da_janela_aerea=True,
                      quando_cotar="rebuscar toda semana")])
    agora, aguardando, _, _ = recotar.classificar(v, HOJE)
    assert agora == [], "nao da para cotar bilhete que nao esta a venda"
    item, motivo = aguardando[0]
    assert "2026-10-03" in motivo, "a espera tem de vir com data, nao com prosa"


def test_sem_preco_e_sem_quando_cotar_e_tarefa_de_hoje():
    """Linha sem preco e sem prazo nao e espera, e esquecimento."""
    v = viagem("2027-05-10", "2027-05-17", [custo("Orfa", valor=None)])
    agora, aguardando, _, _ = recotar.classificar(v, HOJE)
    assert [i for i, _ in agora] == ["Orfa"]
    assert aguardando == []


def test_preco_sem_data_de_consulta_e_tarefa_de_hoje():
    """Numero sem data nao e dado, e lembranca - a disciplina do `dado-datado`."""
    v = viagem("2027-05-10", "2027-05-17", [{"item": "Muda", "valor": 10,
                                             "por_pessoa": False}])
    agora, _, _, _ = recotar.classificar(v, HOJE)
    assert "nao diz quando foi consultado" in agora[0][1]


# --- os arquivos publicos do repo --------------------------------------------


def test_modelo_publico_nao_pede_cotacao_no_dia_em_que_foi_escrito():
    """O modelo tem de nascer verde: quem copia precisa saber que qualquer
    alarme veio da propria edicao, nao do template."""
    import json
    v = json.loads((RAIZ / "viagens" / "_modelo.json").read_text(encoding="utf-8"))
    agora, _, _, sem_vol = recotar.classificar(v, date(2027, 1, 20))
    assert agora == [], f"o modelo pede cotacao sozinho: {agora}"
    assert sem_vol == [], "o modelo deve declarar volatilidade em toda linha"
