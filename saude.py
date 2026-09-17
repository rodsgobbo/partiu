"""Estado dos dados do projeto: o que envelheceu, o que vence, o que falta.

Existe porque `reconferir_em` e `consultado_em` nao servem de nada se ninguem os
ler. Um campo de revalidacao que nenhum programa consulta e comentario, nao
controle - e a diferenca so aparece no dia em que a aliquota mudou e o total
continuou saindo com cara de certo.

Uso:
    python saude.py            # relatorio
    python saude.py --quieto   # so o codigo de saida, para hook ou CI
"""
import argparse, json, shutil, subprocess, sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).parent
VELHO = 180          # dias a partir dos quais um dado merece revisao
MCP = RAIZ / ".mcp.json"


def idade(iso):
    try:
        return (date.today() - date.fromisoformat(iso)).days
    except (ValueError, TypeError):
        return None


def reconferencias(obj, caminho=""):
    """Todo par (caminho, data) de `reconferir_em` na arvore, em qualquer nivel."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "reconferir_em" and isinstance(v, str):
                yield caminho, v
            else:
                sub = f"{caminho}.{k}" if caminho else k
                yield from reconferencias(v, sub)
    elif isinstance(obj, list):
        for n, v in enumerate(obj):
            yield from reconferencias(v, f"{caminho}[{n}]")


def dados():
    """Uma linha por arquivo de dados. Devolve (linhas, problemas)."""
    linhas, problemas = [], []
    for arq in sorted((RAIZ / "dados").rglob("*.json")):
        d = json.loads(arq.read_text(encoding="utf-8"))
        nome = str(arq.relative_to(RAIZ))
        ver = d.get("verificado")
        i = idade(d.get("consultado_em"))

        if i is None:
            estado, detalhe = "pendente", "sem data de consulta"
        elif i > VELHO:
            estado, detalhe = "VELHO", f"{i} dias"
            problemas.append(f"{nome}: dado de {i} dias, revisar")
        else:
            estado, detalhe = "ok", f"{i} dias"

        if ver is False and i is not None:
            estado = "nao verificado"

        # data_do_dado e a idade da fonte la em cima, que pode ser bem maior.
        # Fonte velha e copia velha sao problemas diferentes e pedem acoes
        # opostas: copia atrasada some rodando o atualizar; fonte congelada, nao
        # - nenhuma execucao muda o numero, e so restam o consulado e as
        # ressalvas. Enquanto os dois casos imprimiam a mesma linha, o alarme
        # cobrava uma acao que nao existia, e alarme sem saida e alarme que
        # alguem acaba desligando.
        if (j := idade(d.get("data_do_dado"))) is not None and j > VELHO:
            congelada = d.get("fonte_congelada") or {}
            if idade(congelada.get("reconferido_em")) is None:
                problemas.append(f"{nome}: a FONTE tem {j} dias (nao so a nossa copia)")
                detalhe += f", fonte com {j}"
            else:
                # Nao e anistia: o reconferir_em do bloco mora dentro do JSON e o
                # walker abaixo o acha em qualquer profundidade, entao o alarme
                # volta sozinho na data marcada, sem codigo novo.
                detalhe += f", fonte parada ({j}d), ciente"

        # Procura reconferir_em em qualquer profundidade: a data que mais importa
        # costuma estar aninhada (a da China mora em por_destino.CN), e um check
        # que so olha o topo deixa passar justamente a que decide a viagem.
        for caminho, venc in reconferencias(d):
            r = idade(venc)
            if r is None:
                continue
            onde = f"{nome}[{caminho}]" if caminho else nome
            if r >= 0:
                problemas.append(f"{onde}: reconferencia venceu em {venc}, ha {r} dias")
                estado = "VENCIDO"
            elif r > -45:
                problemas.append(f"{onde}: reconferir ate {venc}, faltam {-r} dias")
                if estado == "ok":
                    estado = "vence em breve"

        linhas.append((nome, estado, detalhe, ver))
    return linhas, problemas


def ferramentas():
    """As dependencias externas que o projeto delega."""
    fora = []
    trvl = None
    if MCP.exists():
        cmd = json.loads(MCP.read_text(encoding="utf-8"))["mcpServers"]["trvl"]["command"]
        trvl = Path(cmd).exists() or shutil.which(cmd) is not None
        if not trvl:
            fora.append("trvl: binario nao encontrado no caminho do .mcp.json")
    return trvl, fora


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--quieto", action="store_true", help="so o codigo de saida")
    a = p.parse_args()

    linhas, problemas = dados()
    trvl, fora = ferramentas()
    problemas += fora

    if not a.quieto:
        print(f"{'Arquivo':<34}{'Estado':<16}{'Idade'}")
        print("-" * 62)
        for nome, estado, detalhe, _ in linhas:
            print(f"{nome:<34}{estado:<16}{detalhe}")
        print()
        print(f"trvl instalado: {'sim' if trvl else 'NAO'}")

        if problemas:
            print(f"\n{len(problemas)} ponto(s) de atencao:")
            for x in problemas:
                print("  -", x)
        else:
            print("\nNada vencido. Dados dentro do prazo e ferramentas no lugar.")

    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
