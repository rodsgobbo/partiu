"""O que precisa ser cotado hoje, e o que ainda nao da para cotar.

O projeto sabia DETECTAR preco velho - o `conferir.py` acusa cotacao com mais de
21 dias - mas nao sabia dizer o que fazer a respeito. Faltava a outra metade: das
linhas pendentes, quais sao acionaveis HOJE e quais so esperam a data chegar.

Sem essa separacao, toda linha sem preco parece uma tarefa atrasada. Numa varredura
de 22/09/2026 havia 27 linhas pendentes nas 6 viagens e **uma** era acionavel; as
outras 26 diziam "a partir de outubro/2026". Lista em que quase tudo e ruido e
lista que ninguem le, e o dia em que a passagem realmente vence passa junto.

Uso:
    python recotar.py                  # todas as viagens
    python recotar.py viagens/x.json   # uma
    python recotar.py --quieto         # so o codigo de saida, para hook ou CI

Sai com 1 se ha algo a cotar hoje.
"""
import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).parent
VIAGENS = RAIZ / "viagens"

# Mesmo limite do conferir.py: cotacao de mais de 21 dias nao e preco, e lembranca.
VENCE_EM = 21

# Ate quantos dias antes da partida uma companhia poe o voo a venda.
#
# DADO DATADO (ver skill `dado-datado`). Companhia abre venda entre ~330 e ~361
# dias antes. Usamos o teto porque o que interessa aqui e "ja da para tentar?" -
# errar para o otimista manda o usuario olhar, errar para o pessimista o faz
# perder a abertura.
#
# Conferido em 22/09/2026 contra o Kiwi, com controle para separar "nao esta a
# venda" de "o backend falhou":
#   GRU->PEK  10/09/2027  353d  -> 15 opcoes   (dentro)
#   PVG->GRU  29/09/2027  372d  -> 0 opcoes    (fora)
#   PVG->GRU  01/06/2027  252d  -> 15 opcoes   (controle: a rota existe)
JANELA_AEREA_DIAS = 361

# Quanto tempo um preco aguenta, por volatilidade declarada na linha de custo.
# Tarifa aerea muda toda semana; uma reserva de imprevisto que voce arbitrou nao
# muda nunca. Tratar as duas com o mesmo prazo e o que produz alarme constante.
PRAZO = {"alta": VENCE_EM, "media": 60, "baixa": 180}
PADRAO = "alta"   # sem declaracao, assume o pior e DIZ que assumiu


def idade(iso, hoje):
    try:
        return (hoje - date.fromisoformat(iso)).days
    except (ValueError, TypeError):
        return None


def janela_aerea(v, hoje):
    """Se a viagem ja pode ter passagem cotada.

    Multitrecho e UM bilhete: nao adianta a ida estar a venda se a volta nao
    esta. Por isso quem manda e o trecho mais distante, nao o mais proximo.
    """
    datas = v.get("datas") or {}
    pontas = []
    for nome in ("ida", "volta"):
        try:
            d = date.fromisoformat(datas[nome])
        except (KeyError, ValueError, TypeError):
            continue
        pontas.append((nome, d, (d - hoje).days))
    if not pontas:
        return None

    fora = [p for p in pontas if p[2] > JANELA_AEREA_DIAS]
    if not fora:
        return {"aberta": True, "pontas": pontas, "abre_em": None}

    # A ponta mais distante e a ultima a entrar na janela, entao e ela que
    # define quando o bilhete inteiro fica cotavel.
    _, d_max, _ = max(fora, key=lambda p: p[2])
    return {"aberta": False, "pontas": pontas,
            "abre_em": d_max - timedelta(days=JANELA_AEREA_DIAS)}


def classificar(v, hoje):
    """Devolve (agora, aguardando, revisar, sem_volatilidade)."""
    agora, aguardando, revisar, sem_vol = [], [], [], []
    janela = janela_aerea(v, hoje)

    for c in v.get("custos", []):
        item = c.get("item", "?")
        vol = c.get("volatilidade")
        if vol not in PRAZO:
            sem_vol.append(item)
            vol = PADRAO

        if c.get("valor") is None:
            # Linha sem preco: e tarefa ou e espera? Se ela depende da janela
            # aerea e a janela esta fechada, e espera com data certa. O resto
            # tem so o `quando_cotar` em prosa, que nenhum programa confere -
            # entao e repassado verbatim, marcado como nao conferivel.
            quando = c.get("quando_cotar") or ""
            if c.get("depende_da_janela_aerea") and janela and not janela["aberta"]:
                aguardando.append((item, f"janela aerea abre ~{janela['abre_em']}"))
            elif quando:
                aguardando.append((item, f'prosa, nao conferivel: "{quando[:58]}"'))
            else:
                agora.append((item, "sem preco e sem quando_cotar"))
            continue

        i = idade(c.get("consultado_em"), hoje)
        if i is None:
            agora.append((item, "tem preco e nao diz quando foi consultado"))
        elif i > PRAZO[vol]:
            destino = agora if vol == "alta" else revisar
            destino.append((item, f"{i}d, limite {PRAZO[vol]}d ({vol})"))

    return agora, aguardando, revisar, sem_vol


def alvos(args):
    if args:
        return [Path(a) for a in args]
    return sorted(VIAGENS.glob("*.json"))


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("arquivos", nargs="*", help="viagens a checar (padrao: todas)")
    p.add_argument("--quieto", action="store_true", help="so o codigo de saida")
    a = p.parse_args()

    hoje = date.today()
    total_agora = 0
    sem_vol_total = 0

    for arq in alvos(a.arquivos):
        v = json.loads(arq.read_text(encoding="utf-8"))
        agora, aguardando, revisar, sem_vol = classificar(v, hoje)
        total_agora += len(agora)
        sem_vol_total += len(sem_vol)
        if a.quieto:
            continue

        print(arq.name)
        j = janela_aerea(v, hoje)
        if j:
            partes = " | ".join(
                f"{nome} {dias}d {'dentro' if dias <= JANELA_AEREA_DIAS else 'FORA'}"
                for nome, _, dias in j["pontas"])
            extra = "" if j["aberta"] else f" - bilhete so a partir de ~{j['abre_em']}"
            print(f"  janela aerea: {partes}{extra}")

        for titulo, linhas in (("COTAR AGORA", agora),
                               ("aguardando", aguardando),
                               ("revisar", revisar)):
            if not linhas:
                continue
            print(f"  {titulo}")
            for item, motivo in linhas:
                print(f"    {item[:48]:<48} {motivo}")
        if not (agora or aguardando or revisar):
            print("  nada pendente")
        print()

    if not a.quieto:
        if sem_vol_total:
            print(f"{sem_vol_total} linha(s) sem `volatilidade` declarada, tratadas como "
                  f"'{PADRAO}' ({PRAZO[PADRAO]}d).")
            print("Declare \"volatilidade\": \"alta\" | \"media\" | \"baixa\" na linha de custo")
            print("para que reserva de imprevisto pare de vencer junto com tarifa aerea.")
        print(f"\n{total_agora} linha(s) para cotar hoje."
              if total_agora else "\nNada para cotar hoje.")

    return 1 if total_agora else 0


if __name__ == "__main__":
    sys.exit(main())
