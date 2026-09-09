"""Custo real, em reais, de gastar moeda estrangeira - por meio de pagamento.

PTAX oficial do Banco Central + IOF + spread. A conta e deterministica de
proposito: taxa de cambio nao e coisa para um modelo estimar de cabeca.

Uso:
    python cambio.py USD 3000
    python cambio.py EUR 1500 --spread-cartao 0.045 --spread-especie 0.02
"""
import argparse, json, urllib.request
from datetime import date, timedelta
from pathlib import Path

DADOS = Path(__file__).resolve().parents[4] / "dados" / "iof.json"
BASE = "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata"

# Spreads padrao: sao CHUTES DE PARTIDA, nao dado apurado. Cada banco e casa de
# cambio cobra o seu, e a diferenca entre 2% e 6% muda o resultado da comparacao.
# Troque pelos numeros do seu banco com --spread-*.
SPREAD_PADRAO = {"cartao": 0.04, "especie": 0.03, "conta_global": 0.01}


def ptax(moeda: str, dias: int = 10) -> tuple[float, str]:
    """Ultima cotacao de venda disponivel. Olha para tras porque nao ha PTAX em
    fim de semana nem feriado."""
    fim, ini = date.today(), date.today() - timedelta(days=dias)
    f = lambda d: d.strftime("%m-%d-%Y")
    if moeda == "USD":
        rota = (f"CotacaoDolarPeriodo(dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)"
                f"?@dataInicial='{f(ini)}'&@dataFinalCotacao='{f(fim)}'")
    else:
        rota = (f"CotacaoMoedaPeriodo(moeda=@moeda,dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)"
                f"?@moeda='{moeda}'&@dataInicial='{f(ini)}'&@dataFinalCotacao='{f(fim)}'")
    url = f"{BASE}/{rota}&$format=json"
    with urllib.request.urlopen(url, timeout=30) as r:
        v = json.load(r)["value"]
    if not v:
        raise SystemExit("fora da PTAX diaria")
    ultima = v[-1]
    return float(ultima["cotacaoVenda"]), ultima["dataHoraCotacao"][:10]


def fechamento(moeda: str, dias: int = 10) -> tuple[float, str]:
    """Boletim de fechamento do BCB: 156 moedas, taxa de venda em reais por
    unidade. Serve para o que a PTAX diaria nao cobre (ARS, CLP, TRY, THB...).
    A coluna 6 ja vem em BRL, entao nao ha cruzamento nem estimativa aqui."""
    algum_dia_baixou = False
    for i in range(dias):
        d = date.today() - timedelta(days=i)
        url = f"https://www4.bcb.gov.br/Download/fechamento/{d:%Y%m%d}.csv"
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                linhas = r.read().decode("latin-1").splitlines()
        except Exception:
            # Dia sem boletim (fim de semana, feriado) e queda de rede caem os
            # dois aqui. Guardamos qual foi para nao dar o diagnostico errado.
            continue
        algum_dia_baixou = True
        for l in linhas:
            c = l.split(";")
            if len(c) > 5 and c[3] == moeda:
                return float(c[5].replace(",", ".")), d.isoformat()
    if not algum_dia_baixou:
        raise SystemExit(f"Nao consegui baixar nenhum boletim do BCB dos ultimos {dias} "
                         f"dias. Isso e falha de acesso, nao problema com {moeda} - "
                         f"confira a conexao antes de mexer no codigo do simbolo.")
    raise SystemExit(f"{moeda} nao aparece no boletim do BCB dos ultimos {dias} dias. "
                     f"Confira o simbolo ISO (ex: ARS, CLP, JPY).")


def em_reais(valor: float, taxa: float, spread: float, taxa_iof: float) -> float:
    """A conta canonica do projeto. Mora aqui, e nao em cada script, porque duas
    copias da mesma formula divergem no primeiro ajuste - e um ajuste de aliquota
    que pega so metade dos lugares e pior que nenhum."""
    return valor * taxa * (1 + spread) * (1 + taxa_iof)


def iof() -> dict:
    return json.loads(DADOS.read_text(encoding="utf-8"))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("moeda")
    p.add_argument("valor", type=float, help="quanto voce vai gastar, na moeda estrangeira")
    for k, v in SPREAD_PADRAO.items():
        p.add_argument(f"--spread-{k.replace('_', '-')}", type=float, default=v,
                       dest=f"spread_{k}", help=f"padrao {v:.1%} (chute, troque pelo do seu banco)")
    a = p.parse_args()

    moeda = a.moeda.upper()
    try:
        cotacao, quando, origem = *ptax(moeda), "PTAX diaria"
    except SystemExit:
        cotacao, quando, origem = *fechamento(moeda), "boletim de fechamento"
    d = iof()
    al = d["aliquotas"]

    print(f"Venda {moeda}/BRL: R$ {cotacao:.4f}  (Banco Central, {origem}, {quando})")
    print(f"Gasto simulado: {a.valor:,.2f} {moeda}\n")

    meios = [
        ("Cartao de credito", al["cartao_credito_internacional"], a.spread_cartao),
        ("Moeda em especie", al["moeda_especie"], a.spread_especie),
        ("Conta global", al["conta_global_transferencia"], a.spread_conta_global),
    ]

    print(f"{'Meio':<20} {'IOF':>7} {'Spread':>8} {'Total BRL':>14}")
    print("-" * 52)
    incerto = False
    for nome, regra, spread in meios:
        taxa = regra.get("valor")
        if taxa is None:
            incerto = True
            print(f"{nome:<20} {'?':>7} {spread:>7.1%} {'nao calculado':>14}")
            continue
        if not regra.get("verificado"):
            incerto = True
        total = em_reais(a.valor, cotacao, spread, taxa)
        marca = "" if regra.get("verificado") else " *"
        print(f"{nome:<20} {taxa:>6.2%}{marca:<1} {spread:>7.1%} {total:>14,.2f}")

    if incerto:
        print("\n" + "=" * 52)
        print("ATENCAO: ha aliquota nao conferida em fonte primaria. Linhas com *")
        print("usam valor de origem secundaria. Trate como estimativa.")
        print(f"Pendencia registrada em: {DADOS}")
    else:
        taxas = {r["valor"] for _, r, _ in meios if r.get("valor") is not None}
        if len(taxas) == 1:
            print(f"\nO IOF e o mesmo ({taxas.pop():.1%}) nos tres meios desde a unificacao")
            print("de 2025. Entao quem decide aqui e o SPREAD, nao o imposto.")

    sj = d.get("status_juridico", {})
    if sj and not sj.get("estavel", True):
        print("\nRessalva juridica:", sj["motivo"].split(".")[0] + ".")
        print("Reconferir a partir de", sj["reconferir_em"])

    print(f"\nIOF: {d['norma']}, conferido em {d['consultado_em']}.")
    print("Spread e chute de partida. Peca o do seu banco e passe em --spread-*.")


if __name__ == "__main__":
    main()
