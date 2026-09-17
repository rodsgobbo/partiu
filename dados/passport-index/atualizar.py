"""Rebaixa o dataset de vistos e regrava br.csv + FONTE.json com a procedencia."""
import csv, io, json, subprocess, sys, urllib.request
from datetime import date
from pathlib import Path

RAW = "https://raw.githubusercontent.com/imorte/passport-index-data/main/passport-index-tidy-iso2.csv"
REPO = "imorte/passport-index-data"
AQUI = Path(__file__).parent


def commit_atual():
    """Pega sha e data do ultimo commit. Sem gh instalado, devolve desconhecido."""
    try:
        out = subprocess.run(
            ["gh", "api", f"repos/{REPO}/commits", "--jq", ".[0].sha + \" \" + .[0].commit.author.date"],
            capture_output=True, text=True, timeout=30, check=True,
        ).stdout.split()
        return out[0][:7], out[1][:10]
    except Exception:
        return "desconhecido", "desconhecido"


def descongelou(fonte, sha):
    """A fonte parada voltou a andar? Fora do main() para poder ser testada sem
    rede: e uma decisao de uma linha que, errada, silencia um alerta para sempre."""
    return "fonte_congelada" in fonte and sha != fonte.get("commit")


def main():
    with urllib.request.urlopen(RAW, timeout=60) as r:
        linhas = list(csv.reader(io.StringIO(r.read().decode("utf-8"))))

    cabecalho, br = linhas[0], [l for l in linhas[1:] if l and l[0] == "BR"]
    if not br:
        sys.exit("Nenhuma linha com passaporte BR: o formato da fonte mudou. Nao sobrescrevi nada.")

    destino = AQUI / "br.csv"
    antes = {}
    if destino.exists():
        with destino.open(encoding="utf-8") as f:
            antes = {r["Destination"]: r["Requirement"] for r in csv.DictReader(f)}

    with destino.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(cabecalho)
        w.writerows(br)

    sha, data_dado = commit_atual()
    fonte = json.loads((AQUI / "FONTE.json").read_text(encoding="utf-8"))
    fonte["consultado_em"] = date.today().isoformat()

    if data_dado == "desconhecido":
        # Preserva a procedencia anterior em vez de sobrescrever com
        # "desconhecido". Data ilegivel silencia o alerta de dado velho do
        # visto.py, e arquivo que se declara verificado sem saber a propria
        # idade e pior que arquivo que se declara duvidoso.
        fonte["verificado"] = False
        fonte["ressalva_atualizacao"] = (
            f"CSV rebaixado em {fonte['consultado_em']}, mas nao foi possivel confirmar "
            "o commit de origem (gh ausente ou sem rede). commit e data_do_dado "
            "sao os da atualizacao anterior.")
        print("AVISO: dados baixados, mas a procedencia nao pode ser confirmada.")
        print("       FONTE.json ficou com verificado=false de proposito.")
    else:
        # `fonte_congelada` justifica calar o alerta de fonte velha, e a
        # justificativa morre no instante em que a fonte anda. Deixar o bloco
        # para tras silenciaria o alerta para sempre com um motivo que deixou de
        # valer - o mesmo modo de falha da procedencia envenenada, so que mais
        # dificil de ver, porque o arquivo estaria dizendo a verdade sobre tudo
        # menos sobre o que importa.
        voltou = descongelou(fonte, sha)
        fonte.update({"commit": sha, "data_do_dado": data_dado, "verificado": True})
        fonte.pop("ressalva_atualizacao", None)
        if voltou:
            fonte.pop("fonte_congelada")
            print("\nA FONTE voltou a andar: bloco fonte_congelada removido.")
            print("Reveja 'confianca' e 'ressalva' - foram rebaixadas enquanto ela")
            print("estava parada, e ninguem mais vai lembrar disso.")
    (AQUI / "FONTE.json").write_text(
        json.dumps(fonte, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Compara par a par em vez de linha de texto: o csv.writer pode aspar um
    # campo, e um join cru acusaria mudanca onde so mudou a formatacao.
    depois = {l[1]: l[2] for l in br if len(l) > 2}
    print(f"{len(br)} destinos gravados (fonte {sha}, dado de {data_dado}).")
    if antes:
        mudou = {d: (antes.get(d), r) for d, r in depois.items() if antes.get(d) != r}
        sumiu = set(antes) - set(depois)
        if mudou:
            print(f"\n{len(mudou)} destino(s) mudaram desde a ultima vez:")
            for d, (de, para) in sorted(mudou.items()):
                print(f"   {d}: {de or 'novo'} -> {para}")
        if sumiu:
            print(f"\n{len(sumiu)} destino(s) sairam: {chr(44).join(sorted(sumiu))}")
        if not mudou and not sumiu:
            print("Nada mudou desde a ultima atualizacao.")


if __name__ == "__main__":
    main()
