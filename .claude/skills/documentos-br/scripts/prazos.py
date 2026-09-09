"""Calendario reverso de documentos, a partir da data da viagem.

Documento e problema de calendario, nao de lista. Saber que "precisa de visto"
nao ajuda; saber que a fila do consulado fecha a janela em tres semanas, sim.

Prazo desconhecido aparece no calendario como desconhecido, nunca some da lista:
o item que voce esqueceu e o que impede o embarque.

Uso:
    python prazos.py 2027-01-15
    python prazos.py 2027-01-15 --exige-visto --exige-civp
"""
import argparse, json
from datetime import date, timedelta
from pathlib import Path

DADOS = Path(__file__).resolve().parents[4] / "dados" / "prazos.json"


def aplicavel(item: dict, a) -> bool:
    """Filtra pelo que o usuario disse sobre a viagem.

    Le o campo `requer`, nunca o texto de `condicao`: filtro que casa substring
    em prosa muda de comportamento quando alguem reescreve uma frase, e a falha
    seria silenciosa - o item some do calendario sem erro nenhum.

    Item sem `requer` aparece sempre. Na duvida mantemos: esquecer um documento
    custa mais que listar um a mais."""
    return {"civp": a.exige_civp, "visto": a.exige_visto,
            "eta": a.exige_eta}.get(item.get("requer"), True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("viagem", help="data da viagem, AAAA-MM-DD")
    p.add_argument("--exige-visto", action="store_true")
    p.add_argument("--exige-civp", action="store_true", help="destino exige certificado de vacinacao")
    p.add_argument("--exige-eta", action="store_true", help="destino exige ETA ou e-visa")
    a = p.parse_args()

    try:
        viagem = date.fromisoformat(a.viagem)
    except ValueError:
        raise SystemExit("Data invalida. Use AAAA-MM-DD, por exemplo 2027-01-15.")

    hoje = date.today()
    faltam = (viagem - hoje).days
    if faltam < 0:
        raise SystemExit(f"A data {viagem} ja passou.")

    d = json.loads(DADOS.read_text(encoding="utf-8"))
    itens = [i for i in d["itens"] if aplicavel(i, a)]

    print(f"Viagem em {viagem:%d/%m/%Y} - faltam {faltam} dias\n")

    com, sem = [], []
    for i in itens:
        (com if i["prazo_dias"] is not None else sem).append(i)
    com.sort(key=lambda i: -i["prazo_dias"])

    if com:
        print("Com prazo conhecido")
        print("-" * 62)
        for i in com:
            limite = viagem - timedelta(days=i["prazo_dias"])
            folga = (limite - hoje).days
            if folga < 0:
                status = f"VENCIDO ha {-folga} d"
            elif folga <= 7:
                status = f"apertado, {folga} d"
            else:
                status = f"{folga} d de folga"
            marca = "" if i["verificado"] else " (prazo nao apurado)"
            print(f"  ate {limite:%d/%m/%Y}  {i['nome']}{marca}")
            print(f"{'':16}{status} - {i['nota'].split('.')[0]}.")

    if sem:
        print("\nPrazo ainda nao apurado - descobrir ANTES de fechar a data")
        print("-" * 62)
        for i in sem:
            print(f"  ?  {i['nome']}")
            print(f"{'':5}{i['nota'].split('.')[0]}.")
        print("\nEsses sao o risco real do calendario: sem o prazo, nao da para")
        print("saber se ainda cabe. Apure e registre em dados/prazos.json.")

    print(f"\nPrazos conferidos em {d['consultado_em']}.")


if __name__ == "__main__":
    main()
