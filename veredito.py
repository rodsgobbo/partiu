"""Comprar a passagem agora, esperar, ou mudar de plano.

As pecas ja existiam soltas: o historico de preco do trvl diz a tendencia, o `recotar.py`
diz a idade da cotacao, o `prazos.py` diz quando o documento obriga a decidir.
Ninguem juntava as tres numa resposta, e quem junta de cabeca costuma esquecer a
que manda: **prazo de documento vence tendencia de preco.** Esperar uma queda que
chega depois da data limite do visto nao e economia.

Com um insumo faltando, o veredito e SEM VEREDITO e diz qual falta. Decidir sem
ele seria a resposta plausivel e errada que o projeto existe para evitar.

Le, por linha de passagem (`depende_da_janela_aerea: true`):
  - `valor`, `consultado_em`, `volatilidade`  -> a cotacao esta viva?
  - `tendencia`                               -> o que o historico de preco mostra
  - `documentos.exige` e `documentos.prazos`  -> ate quando da para decidir

Uso:
    python veredito.py                  # todas as viagens
    python veredito.py viagens/x.json   # uma
    python veredito.py --quieto         # so o codigo de saida

Sai com 1 se alguma linha deu MUDE ou SEM VEREDITO. Nao acessa a rede: a tendencia
entra pelo arquivo, como a cotacao entra no `conferir.py`.
"""
import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import recotar

RAIZ = Path(__file__).parent
PRAZOS = RAIZ / "dados" / "prazos.json"

# Com o prazo do documento a menos disto, esperar deixa de ser opcao mesmo com a
# tendencia caindo: nao sobra tempo para a queda acontecer, ser vista e virar
# compra. NUMERO ARBITRADO, nao apurado - e uma margem de manobra, nao um dado.
MARGEM_DIAS = 14

# Tendencia e previsao de preco, entao estraga no ritmo da tarifa.
TENDENCIA_VENCE_EM = recotar.VENCE_EM

DIRECOES = ("subindo", "estavel", "caindo")


def carregar_prazos():
    return {i["requer"]: i for i in json.loads(PRAZOS.read_text(encoding="utf-8"))["itens"]
            if i.get("requer")}


def limite_documento(v, prazos_gerais):
    """Ate quando da para decidir, pelo documento. Devolve (limite, motivo, faltando).

    `documentos.exige` e a lista do que a viagem precisa (`visto`, `civp`, `eta`,
    os mesmos nomes do `requer` de `dados/prazos.json`). Lista vazia e resposta:
    nada a providenciar. Campo ausente nao e: a `documentos-br` nao foi rodada, ou
    rodou e ficou em prosa.

    O prazo da viagem (`documentos.prazos`, apurado no consulado do destino)
    vence o generico, que quase sempre e null.
    """
    docs = v.get("documentos") or {}
    if docs.get("exige") is None:
        return None, None, "documentos.exige nao declarado - rode a documentos-br"
    try:
        ida = date.fromisoformat(v["datas"]["ida"])
    except (KeyError, ValueError, TypeError):
        return None, None, "datas.ida ausente - sem ela nao ha prazo a contar"

    proprios = docs.get("prazos") or {}
    limites, faltando = [], []
    for req in docs["exige"]:
        p = proprios.get(req)
        if p is not None:
            dias, fonte = p.get("dias"), p.get("fonte") or "sem fonte"
            if p.get("verificado") is False:
                fonte += ", NAO VERIFICADO"
        else:
            geral = prazos_gerais.get(req) or {}
            dias, fonte = geral.get("prazo_dias"), "dados/prazos.json"
        if dias is None:
            faltando.append(req)
            continue
        limites.append((ida - timedelta(days=dias), f"{req}: {dias}d antes da ida ({fonte})"))

    if faltando:
        return None, None, ("prazo nao apurado para " + ", ".join(faltando)
                            + " - registre em documentos.prazos")
    if not limites:
        return None, None, None          # nada a providenciar: nao limita
    limite, motivo = min(limites)
    return limite, motivo, None


def ler_tendencia(c, hoje):
    """Devolve (tendencia, faltando)."""
    t = c.get("tendencia")
    if not t:
        return None, ("sem tendencia - leia `trvl watch history` da rota (crie com "
                      "`trvl watch add`) e grave em `tendencia`")
    if t.get("direcao") not in DIRECOES:
        return None, f"tendencia.direcao deve ser {'/'.join(DIRECOES)}"
    i = recotar.idade(t.get("consultado_em"), hoje)
    if i is None:
        return None, "tendencia sem consultado_em"
    if i > TENDENCIA_VENCE_EM:
        return None, f"tendencia de {i}d, limite {TENDENCIA_VENCE_EM}d - releia o watch history"
    return t, None


def ler_cotacao(c, janela, hoje):
    """Devolve (espera_ate, faltando). `espera_ate` so quando a janela esta fechada."""
    if janela and not janela["aberta"]:
        return janela["abre_em"], None
    if c.get("valor") is None:
        return None, "sem preco e a janela esta aberta - cote antes"
    vol = c.get("volatilidade") if c.get("volatilidade") in recotar.PRAZO else recotar.PADRAO
    i = recotar.idade(c.get("consultado_em"), hoje)
    if i is None:
        return None, "preco sem consultado_em"
    if i > recotar.PRAZO[vol]:
        return None, f"cotacao de {i}d, limite {recotar.PRAZO[vol]}d ({vol}) - recote"
    return None, None


def posicao_na_faixa(c, t):
    """'acima', 'dentro', 'abaixo', ou None quando nao da para comparar."""
    f = t.get("faixa") or {}
    if f.get("min") is None or f.get("max") is None or c.get("valor") is None:
        return None
    if f.get("moeda", c.get("moeda")) != c.get("moeda"):
        return None                      # sem conversao aqui: comparar exigiria cotacao
    if c["valor"] > f["max"]:
        return "acima"
    if c["valor"] < f["min"]:
        return "abaixo"
    return "dentro"


def decidir(v, c, hoje, prazos_gerais):
    """O veredito de uma linha de passagem.

    Devolve um dict com `veredito` (RESERVE, ESPERE, MUDE, SEM VEREDITO),
    `decidiu` (qual insumo mandou), `motivo`, `faltando` e `ate`.
    """
    janela = recotar.janela_aerea(v, hoje)
    limite, motivo_doc, falta_doc = limite_documento(v, prazos_gerais)

    def r(veredito, decidiu, motivo, faltando=(), ate=None):
        return {"veredito": veredito, "decidiu": decidiu, "motivo": motivo,
                "faltando": list(faltando), "ate": ate, "limite_doc": limite}

    # 1. Documento que ja nao sai a tempo decide sozinho, com ou sem o resto:
    #    nenhum preco salva uma viagem em que nao se embarca.
    if limite is not None and limite < hoje:
        return r("MUDE", "documento",
                 f"o prazo do documento venceu em {limite} ({motivo_doc})")

    espera_ate, falta_cot = ler_cotacao(c, janela, hoje)

    # 2. Bilhete que nao esta a venda: esperar e a unica opcao - a menos que a
    #    venda abra depois do limite do documento.
    if espera_ate is not None:
        if limite is not None and espera_ate > limite:
            return r("MUDE", "documento",
                     f"a venda abre ~{espera_ate}, depois do limite do documento em "
                     f"{limite} ({motivo_doc})")
        faltando = [falta_doc] if falta_doc else []
        return r("ESPERE", "janela aerea",
                 f"o bilhete ainda nao esta a venda; abre ~{espera_ate}",
                 faltando, ate=espera_ate)

    t, falta_tend = ler_tendencia(c, hoje)
    faltando = [f for f in (falta_doc, falta_cot, falta_tend) if f]
    if faltando:
        return r("SEM VEREDITO", None, "falta insumo para decidir", faltando)

    folga = (limite - hoje).days if limite is not None else None
    faixa = posicao_na_faixa(c, t)
    quer_esperar = t["direcao"] == "caindo" or (t["direcao"] == "estavel" and faixa == "acima")

    if quer_esperar:
        if folga is not None and folga <= MARGEM_DIAS:
            return r("RESERVE", "documento",
                     f"a tendencia pede espera, mas o documento so da {folga}d "
                     f"({motivo_doc})")
        porque = ("tendencia caindo" if t["direcao"] == "caindo"
                  else "preco acima da faixa historica, tendencia estavel")
        if limite is not None:
            ate = limite - timedelta(days=MARGEM_DIAS)
            return r("ESPERE", "tendencia", f"{porque}; decida ate {ate}", ate=ate)
        return r("ESPERE", "tendencia",
                 f"{porque}; sem documento limitando - releia o watch history em "
                 f"{TENDENCIA_VENCE_EM}d", ate=hoje + timedelta(days=TENDENCIA_VENCE_EM))

    if t["direcao"] == "subindo":
        return r("RESERVE", "tendencia", "tendencia subindo")
    detalhe = {"abaixo": "preco abaixo da faixa historica",
               "dentro": "preco dentro da faixa historica",
               None: "sem faixa historica comparavel"}[faixa]
    return r("RESERVE", "tendencia", f"tendencia estavel, {detalhe}: esperar nao rende")


def passagens(v):
    return [c for c in v.get("custos", []) if c.get("depende_da_janela_aerea")]


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("arquivos", nargs="*", help="viagens a checar (padrao: todas)")
    p.add_argument("--quieto", action="store_true", help="so o codigo de saida")
    a = p.parse_args()

    hoje = date.today()
    prazos_gerais = carregar_prazos()
    pendente = 0

    for arq in recotar.alvos(a.arquivos):
        v = json.loads(arq.read_text(encoding="utf-8"))
        linhas = passagens(v)
        if not a.quieto:
            print(arq.name)
            if not linhas:
                print("  nenhuma linha com depende_da_janela_aerea - nada a decidir aqui\n")
        for c in linhas:
            d = decidir(v, c, hoje, prazos_gerais)
            if d["veredito"] in ("MUDE", "SEM VEREDITO"):
                pendente += 1
            if a.quieto:
                continue
            print(f"  {c.get('item', '?')[:56]}")
            print(f"    {d['veredito']}" + (f"  (decidiu: {d['decidiu']})" if d["decidiu"] else ""))
            print(f"    {d['motivo']}")
            if d["limite_doc"] is not None and d["decidiu"] != "documento":
                print(f"    limite do documento: {d['limite_doc']}")
            for f in d["faltando"]:
                print(f"    falta: {f}")
        if linhas and not a.quieto:
            print()

    return 1 if pendente else 0


if __name__ == "__main__":
    sys.exit(main())
