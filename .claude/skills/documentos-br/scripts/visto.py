"""Exigencia de visto para o passaporte brasileiro, por destino.

Existe porque a ferramenta equivalente do trvl responde "visa-required" para
TODO destino quando o passaporte e BR - o dataset dela nao tem o Brasil como
passaporte. Aqui a resposta vem de dado real, com a data do dado junto.

Uso:
    python visto.py FR
    python visto.py FR PT JP US
    python visto.py --listar-sem-visto
"""
import argparse, csv, json
from datetime import date
from pathlib import Path

DADOS = Path(__file__).resolve().parents[4] / "dados" / "passport-index"
RESSALVAS = Path(__file__).resolve().parents[4] / "dados" / "visto-ressalvas.json"

LEGENDA = {
    "visa required": "visto exigido - tirar antes de viajar",
    "visa on arrival": "visto na chegada",
    "e-visa": "visto eletronico - solicitar online antes",
    "eta": "autorizacao eletronica (ETA) - solicitar online antes",
    "visa free": "sem visto",
    "no admission": "entrada nao permitida",
}


def carregar() -> tuple[dict, dict]:
    fonte = json.loads((DADOS / "FONTE.json").read_text(encoding="utf-8"))
    with (DADOS / "br.csv").open(encoding="utf-8") as f:
        linhas = {r["Destination"]: r["Requirement"] for r in csv.DictReader(f)}
    return linhas, fonte


def envelhecimento(iso: str) -> int | None:
    """Dias desde a data do dado. None se a data nao for legivel - preferimos
    nao alertar a alertar errado."""
    try:
        return (date.today() - date.fromisoformat(iso)).days
    except (ValueError, TypeError):
        return None


def descrever(req: str) -> str:
    if req.isdigit():
        return f"sem visto, ate {req} dias"
    return LEGENDA.get(req.lower(), req)


def ressalva_de(destino: str) -> dict | None:
    """Ressalva especifica do destino, quando existe.

    O dataset diz so o estado atual: "CN: 30 dias". Nao tem campo de validade,
    entao politica temporaria aparece com cara de permanente. Para viagem
    futura essa diferenca decide se a pessoa embarca."""
    if not RESSALVAS.exists():
        return None
    d = json.loads(RESSALVAS.read_text(encoding="utf-8"))
    return d.get("por_destino", {}).get(destino)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("destinos", nargs="*", help="codigos ISO-2, ex: FR PT JP")
    p.add_argument("--listar-sem-visto", action="store_true",
                   help="todos os destinos onde brasileiro entra sem visto")
    a = p.parse_args()

    linhas, fonte = carregar()

    if a.listar_sem_visto:
        livres = sorted(d for d, r in linhas.items() if r.isdigit() or r.lower() == "visa free")
        print(f"{len(livres)} destinos sem visto para passaporte brasileiro:\n")
        print(", ".join(livres))
    elif a.destinos:
        largura = max(len(d) for d in a.destinos)
        for d in (x.upper() for x in a.destinos):
            req = linhas.get(d)
            print(f"{d:<{largura}}  {descrever(req) if req else 'destino nao encontrado no dataset'}")
            if (r := ressalva_de(d)):
                print(f"{'':<{largura}}  ATENCAO: essa regra vale ate {r['valido_ate']}")
                print(f"{'':<{largura}}  {r['alerta']}")
                print(f"{'':<{largura}}  Fonte: {r['fonte']}")
    else:
        p.print_help()
        return

    idade = envelhecimento(fonte["data_do_dado"])
    congelada = fonte.get("fonte_congelada")
    if idade and idade > 180:
        # O alerta vem ANTES da ressalva porque muda o que fazer agora: com dado
        # velho a resposta acima pode estar errada, nao apenas incompleta.
        print(f"\n{chr(33) * 52}")
        print(f"DADO COM {idade // 30} MESES. Regra de visto muda sem aviso - a China")
        print("deixou de exigir visto de brasileiro entre duas versoes deste mesmo")
        print("dataset.")
        if congelada:
            # Mandar rodar a atualizacao aqui seria mentira: a fonte parou, e
            # rodar rebaixa o mesmo CSV. Alarme que aponta a acao errada gasta a
            # confianca que o proximo alarme vai precisar.
            print(f"A FONTE parou de ser atualizada (conferido em "
                  f"{congelada['reconferido_em']}):")
            print("rodar a atualizacao NAO resolve. Confirme no consulado e")
            print("registre em dados/visto-ressalvas.json antes de comprar passagem.")
        else:
            print("Rode a atualizacao antes de confiar na resposta acima:")
            print(f"  {fonte['como_atualizar']}")
        print(chr(33) * 52)

    print(f"\nDado de {fonte['data_do_dado']} (commit {fonte['commit']}), baixado em {fonte['consultado_em']}.")
    print(f"Confianca: {fonte['confianca']}.")
    print(fonte["ressalva"])
    if not congelada and (not idade or idade <= 180):
        print(f"Desatualizou? {fonte['como_atualizar']}")


if __name__ == "__main__":
    main()
