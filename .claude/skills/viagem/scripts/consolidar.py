"""Custo total de uma viagem, em reais, a partir do arquivo de estado.

E a pergunta que nenhuma ferramenta de viagem responde: passagem + bagagem +
hotel com taxa + IOF do gasto, tudo somado, na moeda em que voce paga.

Reaproveita o cambio.py em vez de reimplementar cotacao e IOF - duas contas de
cambio no mesmo projeto divergem no primeiro ajuste.

Uso:
    python consolidar.py ../../../../viagens/exemplo-lisboa-2027-03.json
"""
import argparse, importlib.util, json
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[4]
CAMBIO = RAIZ / ".claude" / "skills" / "cambio-br" / "scripts" / "cambio.py"
IDADE_MAXIMA = 21   # dias; acima disso a cotacao vira lembranca, nao preco

# meio de pagamento -> (chave no iof.json, chave no SPREAD_PADRAO). Um mapa so,
# porque dois mapas do mesmo conceito saem de sincronia sem ninguem notar.
MEIOS = {
    "cartao_credito": ("cartao_credito_internacional", "cartao"),
    "moeda_especie": ("moeda_especie", "especie"),
    "conta_global": ("conta_global_transferencia", "conta_global"),
}


def carregar_cambio():
    spec = importlib.util.spec_from_file_location("cambio", CAMBIO)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def linha_em_brl(custo: dict, taxa: float, spread: float, taxa_iof: float,
                 pessoas: int, cb=None, sobretaxa: float = 0.0) -> float:
    """Converte uma linha de custo para reais.

    Duas regras moram aqui porque sao faceis de errar a mao e caras quando erram:
    valor ja em BRL nao sofre conversao nem IOF (IOF de cambio incide sobre
    operacao de cambio, e nao houve nenhuma), e `por_pessoa` multiplica pelo
    numero de viajantes antes de tudo.

    `sobretaxa` e a do destino, e so quem chama sabe se ela incide nesta linha:
    ela e da moeda de la, nao de tudo que e estrangeiro.

    `cb` e o modulo cambio, dono da formula. Fica opcional so para o teste poder
    chamar sem carregar o modulo por caminho."""
    if cb is None:
        cb = carregar_cambio()
    bruto = custo["valor"] * (pessoas if custo.get("por_pessoa") else 1)
    if custo["moeda"] == "BRL":
        return bruto
    return cb.em_reais(bruto, taxa, spread, taxa_iof, sobretaxa)


def cotar(cb, moeda):
    """Devolve (taxa_brl, origem, data). BRL nao converte."""
    if moeda == "BRL":
        return 1.0, "ja em reais", None
    try:
        v, q = cb.ptax(moeda)
        return v, "PTAX diaria", q
    except SystemExit:
        v, q = cb.fechamento(moeda)
        return v, "boletim de fechamento", q


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("arquivo")
    a = p.parse_args()

    v = json.loads(Path(a.arquivo).read_text(encoding="utf-8"))
    cb = carregar_cambio()
    iof = cb.iof()

    meio = v.get("meio_pagamento", "cartao_credito")
    if meio not in MEIOS:
        raise SystemExit(f"meio_pagamento invalido: {meio!r}. "
                         f"Use um de: {', '.join(MEIOS)}.")
    chave_iof, chave_spread = MEIOS[meio]

    regra = iof["aliquotas"][chave_iof]
    taxa_iof = regra["valor"]
    if taxa_iof is None:
        raise SystemExit(f"A aliquota de IOF para {meio} esta em conflito de fontes "
                         f"em dados/iof.json e nao da para somar um total honesto. "
                         f"Resolva a pendencia ou escolha outro meio_pagamento.")

    spread = v.get("spread")
    spread_chutado = spread is None
    if spread_chutado:
        spread = cb.SPREAD_PADRAO[chave_spread]

    pessoas = v.get("viajantes", 1)
    if not isinstance(pessoas, int) or pessoas < 1:
        raise SystemExit(f"viajantes deve ser inteiro >= 1, veio {pessoas!r}.")
    print(f"{v['destino']['cidade']} ({v['destino']['pais']}) - "
          f"{v['datas']['ida']} a {v['datas']['volta']}, {pessoas} viajante(s)")
    # A sobretaxa e do destino: incide no gasto na moeda de la, nao em tudo que e
    # estrangeiro. O eSIM comprado em dolar no Brasil nao passa pelo Alipay, e
    # aplicar nele a taxa do app chines seria inventar custo.
    moeda_local = v.get("moeda_local")
    sobretaxa, fonte_sobretaxa, avisos_sobretaxa = 0.0, None, []
    achada = cb.sobretaxa_do_destino(v["destino"]["pais"])
    if achada:
        sobretaxa, fonte_sobretaxa, isencao = achada
        if isinstance(isencao, dict) and isencao.get("valido_ate"):
            fim = isencao["valido_ate"]
            try:
                antes = date.fromisoformat(fim) < date.fromisoformat(v["datas"]["ida"])
            except ValueError:
                antes = False
            # Nao chamar de `regra`: esse nome ja e a aliquota do IOF, lida acima e
            # consultada depois da tabela. Sobrescreve-la com o texto da isencao
            # quebrava o consolidar em todo destino com sobretaxa e prazo de isencao.
            descricao = isencao.get("regra", "sem descricao")
            if antes:
                avisos_sobretaxa.append(
                    f"A isencao ({descricao}) vale ate {fim}, antes da ida: nao "
                    f"alcanca esta viagem. A sobretaxa entra inteira.")
            else:
                # Isencao valida mas por valor de compra: sem as compras, nao ha
                # como aplicar. Entra inteira, e o aviso diz que o total e teto.
                avisos_sobretaxa.append(
                    f"Ha isencao valida na viagem ({descricao}), mas ela depende do "
                    f"valor de cada compra, que ainda nao existe. A sobretaxa entra "
                    f"inteira: o total e teto, nao estimativa.")

    print(f"Pagando com: {meio.replace('_', ' ')} | IOF {taxa_iof:.1%} | spread {spread:.1%}"
          + (f" | sobretaxa {sobretaxa:.1%} em {moeda_local}" if sobretaxa else ""))
    if fonte_sobretaxa:
        print(f"Sobretaxa do destino lida de {fonte_sobretaxa}.")
        for aviso in avisos_sobretaxa:
            print(aviso)
    print()
    print(f"{'Item':<38}{'Original':>14}{'Em BRL':>14}")
    print("-" * 66)

    if not v["custos"]:
        raise SystemExit(
            "'custos' esta vazio: nao ha o que somar, e um total de 0,00 sairia "
            "com cara de\nresposta. Se a viagem tem custo conhecido, ele mora "
            "em custos[] - e o unico\nlugar que este script le. Veja "
            "viagens/_esquema.md.")

    total = 0.0
    velhos, cotacoes, sem_preco = [], {}, []
    for c in v["custos"]:
        # Linha sem preco e conhecida e nao orcada - duas coisas diferentes de
        # inexistente. Mesma decisao do prazos.py com prazo nao apurado: sai em
        # secao propria em vez de sumir, porque sumir daria a impressao de total
        # fechado, e o que falta aqui costuma ser a linha mais cara da viagem.
        if c.get("valor") is None:
            sem_preco.append(c)
            continue
        moeda = c["moeda"]
        if moeda not in cotacoes:
            cotacoes[moeda] = cotar(cb, moeda)
        taxa, origem, quando = cotacoes[moeda]
        sob = sobretaxa if moeda == moeda_local else 0.0
        brl = linha_em_brl(c, taxa, spread, taxa_iof, pessoas, cb, sob)
        total += brl
        sufixo = "/pessoa" if c.get("por_pessoa") else ""
        print(f"{c['item'][:37]:<38}{c['valor']:>10,.2f} {moeda:<3}{brl:>14,.2f}")
        if sufixo:
            print(f"{'':<38}{'x' + str(pessoas):>14}")
        # A carga por componente, e nao um percentual unico: e o que deixa ver que
        # a sobretaxa entrou numa linha e nao na outra.
        if moeda != "BRL":
            partes = f"spread {spread:.1%} + IOF {taxa_iof:.1%}"
            if sob:
                partes += f" + sobretaxa {sob:.1%}"
            print(f"    carga: {partes}")
        try:
            if (date.today() - date.fromisoformat(c["consultado_em"])).days > IDADE_MAXIMA:
                velhos.append((c["item"], c["consultado_em"]))
        except (KeyError, ValueError):
            velhos.append((c["item"], "sem data"))

    if sem_preco:
        print()
        print("Sem preco - conhecido, nao orcado")
        print("-" * 66)
        for c in sem_preco:
            sufixo = f" (x{pessoas}, por pessoa)" if c.get("por_pessoa") else ""
            print(f"  ?  {c['item']}{sufixo}")
            if c.get("estimativa"):
                print(f"     estimativa nao cotada: {c['estimativa']}")
            if c.get("quando_cotar"):
                print(f"     cotar em: {c['quando_cotar']}")

    print("-" * 66)
    rotulo = "PARCIAL (falta o que esta sem preco)" if sem_preco else "TOTAL"
    print(f"{rotulo:<38}{'':>14}{total:>14,.2f}")
    print(f"{'por pessoa':<38}{'':>14}{total / pessoas:>14,.2f}")

    if sem_preco:
        print(f"\n{len(sem_preco)} linha(s) sem preco: o numero acima e PISO, nao total.")
        print("Somar so o que ja tem preco e como o orcamento fica menor quanto")
        print("menos voce pesquisou - a linha que falta costuma ser a mais cara.")

    brl_only = [c for c in v["custos"]
                if c["moeda"] == "BRL" and c.get("valor") is not None]
    if brl_only:
        print(f"\n{len(brl_only)} linha(s) ja em reais nao levaram IOF de cambio - "
              "e imposto de\noperacao de cambio, e nao houve operacao de cambio nelas.")

    if spread_chutado:
        print("\nO spread usado e o padrao do script, nao o do seu banco. Como o IOF")
        print("ficou igual nos tres meios desde 2025, o spread e o que decide - vale")
        print("levantar o seu e gravar em 'spread' neste arquivo.")

    if velhos:
        print("\nCotacoes envelhecidas (mais de "
              f"{IDADE_MAXIMA} dias) - reconsultar antes de decidir:")
        for item, quando in velhos:
            print(f"  - {item}: {quando}")

    # A disciplina do projeto (dado-datado) e dizer junto do numero quando ele
    # nao foi conferido. O cambio.py ja fazia; aqui o total saia silencioso.
    if not regra.get("verificado"):
        print("\nATENCAO: a aliquota de IOF usada nao foi conferida em fonte")
        print("primaria. O total acima e estimativa, nao conta fechada.")

    sj = iof.get("status_juridico", {})
    if sj and not sj.get("estavel", True):
        print("\nRessalva juridica:", sj["motivo"].split(".")[0] + ".")
        print("Reconferir a partir de", sj.get("reconferir_em", "?"))

    print(f"\nIOF: {iof['norma']}, conferido em {iof['consultado_em']}.")


if __name__ == "__main__":
    main()
