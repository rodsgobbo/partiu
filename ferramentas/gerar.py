# -*- coding: utf-8 -*-
"""Gera o roteiro em HTML para levar na viagem, com custos calculados de verdade.

O roteiro de exemplo vive no textos.py; as datas e o numero de viajantes ficam
no bloco "Sua viagem", logo abaixo dos imports."""
import html
import importlib.util
import sys
from datetime import date, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
RAIZ = BASE.parent
sys.path.insert(0, str(BASE))
import textos as T  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "cambio", RAIZ / ".claude/skills/cambio-br/scripts/cambio.py")
cb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cb)
TAXA, _ = cb.fechamento("CNY")
IOF = cb.iof()["aliquotas"]["cartao_credito_internacional"]["valor"]
brl = lambda y: round(cb.em_reais(y, TAXA, 0.04, IOF))
fmt = lambda v: f"{v:,}".replace(",", ".")

# --- Sua viagem -------------------------------------------------------------
# Valores de exemplo. Troque pelos seus: sao os unicos dados de viagem que o
# gerador precisa, o resto do roteiro vem do textos.py.
INICIO = date(2028, 9, 20)   # primeiro dia; os demais saem em sequencia
VIAJANTES = 2                # quantas pessoas vao
# ----------------------------------------------------------------------------

# eSIM: cobrado em dolar, no cartao, entao leva IOF como qualquer compra externa.
# Uma linha por viajante.
ESIM_USD_POR_LINHA, ESIM_LINHAS = 32, VIAJANTES
usd, _ = cb.ptax("USD")
ESIM_BRL = round(cb.em_reais(ESIM_USD_POR_LINHA * ESIM_LINHAS, usd, 0.04, IOF))

CHINES = {"Pequim": "\u5317\u4eac", "Xi'an": "\u897f\u5b89",
          "Chengdu": "\u6210\u90fd", "Xangai": "\u4e0a\u6d77"}
SELOS = {"destaque": '<span class="selo estrela">imperdível</span>',
         "opcional": '<span class="selo talvez">a combinar</span>',
         "trem": '<span class="selo meio">trem-bala</span>',
         "voo": '<span class="selo meio">voo</span>'}

blocos, cidade_atual = [], None
for i, (cidade, titulo, texto, cny, tag) in enumerate(T.DIAS):
    if cidade != cidade_atual and cidade != "voo":
        cidade_atual = cidade
        n = sum(1 for c, *_ in T.DIAS if c == cidade)
        blocos.append(
            '<section class="estacao">\n'
            '  <div class="estacao-marca" aria-hidden="true"></div>\n'
            f'  <span class="han">{CHINES[cidade]}</span>\n'
            f'  <h2>{html.escape(cidade)}</h2>\n'
            f'  <p class="sub">{html.escape(T.SUBTITULO[cidade])} &middot; {n} dias</p>\n'
            '</section>')
    dia = INICIO + timedelta(days=i)
    classe = f' {tag}' if tag in ("destaque", "opcional") else ""
    custo = ('<span class="livre">sem custo</span>' if cny == 0 else
             f'<span class="brl">R$ {fmt(brl(cny))}</span>'
             f'<span class="cny">&yen; {fmt(cny)}</span>')
    blocos.append(
        f'<article class="dia{classe}">\n'
        f'  <div class="marcador"><span class="num">{i + 1}</span>'
        f'<span class="data">{dia:%d/%m}</span></div>\n'
        f'  <div class="conteudo">\n'
        f'    <h3>{html.escape(titulo)}{SELOS.get(tag, "")}</h3>\n'
        f'    <p>{html.escape(texto)}</p>\n'
        f'  </div>\n'
        f'  <div class="custo">{custo}</div>\n'
        f'</article>')

antes_blocos = "\n  ".join(
    '<div class="check">\n'
    # preco e numero de linhas vem do calculo, nunca do texto: cambio muda,
    # numero de viajantes muda, e o texto nao sabe de nenhum dos dois
    f'    <h3>{titulo} <span class="preco">{preco.format(preco=f"R$ {fmt(ESIM_BRL)}", linhas=ESIM_LINHAS)}</span></h3>\n'
    + "\n".join(f'    <p>{par}</p>' for par in paragrafos) + '\n'
    '  </div>'
    for titulo, preco, paragrafos in T.ANTES)

golpes_blocos = "\n    ".join(
    f'<div class="golpe"><h3>{t}</h3><p>{d}</p></div>' for t, d in T.GOLPES)

praticos_itens = "\n      ".join(f'<li>{p}</li>' for p in T.PRATICOS)
emergencia_linhas = "\n      ".join(
    f'<tr><td>{n}</td><td class="v tel">{t}</td></tr>' for n, t in T.EMERGENCIA)

MESES = ("janeiro", "fevereiro", "marco", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro")
DIAS_TOTAL = len(T.DIAS)
FIM = INICIO + timedelta(days=DIAS_TOTAL - 1)
CIDADES_TOTAL = len({c for c, *_ in T.DIAS if c != "voo"})
periodo = (f"{INICIO.day} a {FIM.day} de {MESES[FIM.month - 1]} de {FIM.year}"
           if (INICIO.month, INICIO.year) == (FIM.month, FIM.year) else
           f"{INICIO.day} de {MESES[INICIO.month - 1]} a "
           f"{FIM.day} de {MESES[FIM.month - 1]} de {FIM.year}")

passeios_cny = sum(d[3] for d in T.DIAS)
transporte_cny = sum(v for _, v in T.EXTRAS)
linhas_extras = "\n      ".join(
    f'<tr><td>{html.escape(nome)}</td><td class="v">&yen; {fmt(v)}</td>'
    f'<td class="v">R$ {fmt(brl(v))}</td></tr>' for nome, v in T.EXTRAS)
total_brl = brl(passeios_cny) + brl(transporte_cny) + ESIM_BRL

css = """
:root{--papel:#e9eee9;--superficie:#f6f9f6;--tinta:#16201c;--tinta-fraca:#5c6a63;
--linha:#ccd8ce;--cinabrio:#bc4229;--jade:#367a60;--ocre:#8f6620;
--sombra:0 1px 2px rgba(22,32,28,.05),0 8px 22px -12px rgba(22,32,28,.28);
--display:"Fraunces",Georgia,"Times New Roman",serif;
--corpo:"Atkinson Hyperlegible","Segoe UI",system-ui,sans-serif;
--mono:"IBM Plex Mono",ui-monospace,Consolas,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
--papel:#0e1411;--superficie:#18211d;--tinta:#e4ebe6;--tinta-fraca:#94a39b;
--linha:#2a3733;--cinabrio:#ea7259;--jade:#6fb994;--ocre:#d6a552;
--sombra:0 1px 2px rgba(0,0,0,.45),0 10px 26px -14px rgba(0,0,0,.8)}}
:root[data-theme="dark"]{
--papel:#0e1411;--superficie:#18211d;--tinta:#e4ebe6;--tinta-fraca:#94a39b;
--linha:#2a3733;--cinabrio:#ea7259;--jade:#6fb994;--ocre:#d6a552;
--sombra:0 1px 2px rgba(0,0,0,.45),0 10px 26px -14px rgba(0,0,0,.8)}
*,*::before,*::after{box-sizing:border-box}
body{margin:0;background:var(--papel);color:var(--tinta);
font:400 1.04rem/1.65 var(--corpo);-webkit-font-smoothing:antialiased}
.envelope{max-width:56rem;margin:0 auto;padding:clamp(1.5rem,4vw,3.5rem) clamp(1rem,4vw,2rem) 4rem}
h1,h2,h3{font-family:var(--display);text-wrap:balance;margin:0;line-height:1.14}
:focus-visible{outline:2px solid var(--cinabrio);outline-offset:3px;border-radius:3px}
.capa{border-bottom:1px solid var(--linha);padding-bottom:2.4rem}
.olho{font:600 .72rem/1 var(--mono);letter-spacing:.16em;text-transform:uppercase;
color:var(--cinabrio);display:block;margin-bottom:1.1rem}
.capa h1{font-size:clamp(2.5rem,8.5vw,4.5rem);font-weight:600;letter-spacing:-.022em}
.capa h1 em{font-style:normal;color:var(--jade)}
.linha-fina{color:var(--tinta-fraca);font-size:1.08rem;margin:1.15rem 0 0;max-width:36em}
.fatos{display:flex;flex-wrap:wrap;gap:1rem 2.4rem;margin:2.1rem 0 0;padding:0}
.fato{display:flex;flex-direction:column;gap:.2rem}
.fato dt{font:600 .67rem/1 var(--mono);letter-spacing:.13em;text-transform:uppercase;color:var(--tinta-fraca)}
.fato dd{margin:0;font-family:var(--display);font-size:1.32rem;font-weight:600;font-variant-numeric:tabular-nums}
.antes{margin:2.6rem 0 0;border:1px solid var(--linha);border-left:3px solid var(--jade);
border-radius:3px;background:var(--superficie);padding:1.3rem 1.4rem}
.antes h2{font-size:1.2rem;font-weight:600;display:flex;align-items:baseline;
justify-content:space-between;gap:1rem;flex-wrap:wrap}
.antes h2 .preco{font:600 1rem/1 var(--mono);color:var(--ocre);font-variant-numeric:tabular-nums}
.antes p{margin:.6rem 0 0;color:var(--tinta-fraca);font-size:.97rem;max-width:62ch}
.antes-intro{font-size:1rem}
.check{margin-top:1.6rem;padding-top:1.3rem;border-top:1px solid var(--linha)}
.check h3{font-size:1.1rem;font-weight:600;display:flex;flex-wrap:wrap;align-items:baseline;
justify-content:space-between;gap:.6rem}
.check h3 .preco{font:600 .78rem/1 var(--mono);color:var(--ocre);letter-spacing:.02em;
font-variant-numeric:tabular-nums;white-space:nowrap}
.cuidados{margin-top:3.2rem;border:1px solid var(--linha);border-left:3px solid var(--cinabrio);
border-radius:3px;padding:clamp(1.3rem,4vw,2rem)}
.cuidados h2{font-size:1.5rem;font-weight:600}
.cuidados p{color:var(--tinta-fraca);margin:.6rem 0 0;max-width:62ch;font-size:.97rem}
.golpes{display:grid;gap:1.2rem;margin-top:1.5rem}
@media (min-width:640px){.golpes{grid-template-columns:1fr 1fr}}
.golpe{background:var(--superficie);border:1px solid var(--linha);border-radius:3px;padding:1.1rem}
.golpe h3{font-size:1.02rem;font-weight:600}
.golpe p{margin-top:.45rem;font-size:.92rem}
.regra{margin-top:1.5rem !important;padding:.9rem 1.1rem;background:var(--superficie);
border:1px dashed var(--cinabrio);border-radius:3px;color:var(--tinta) !important}
.menor{font-size:.9rem !important}
.praticos{margin:1.5rem 0 0;padding-left:1.15rem;color:var(--tinta-fraca);font-size:.94rem}
.praticos li{margin-top:.45rem;max-width:60ch}
.fones{margin-top:1.8rem}
td.tel{font-weight:600;color:var(--tinta)}
.jornada{position:relative;padding-left:clamp(2.7rem,7vw,4rem)}
.jornada::before{content:"";position:absolute;left:clamp(.9rem,2.4vw,1.45rem);top:2rem;bottom:1rem;
width:2px;background:var(--linha)}
.estacao{position:relative;margin:3.4rem 0 1.6rem}
.estacao-marca{position:absolute;left:calc(-1*clamp(2.7rem,7vw,4rem) + clamp(.9rem,2.4vw,1.45rem) - 6px);
top:.7rem;width:14px;height:14px;border-radius:50%;background:var(--cinabrio);box-shadow:0 0 0 5px var(--papel)}
.han{font-family:var(--display);font-size:.92rem;color:var(--cinabrio);letter-spacing:.34em;display:block}
.estacao h2{font-size:clamp(1.65rem,4.5vw,2.2rem);font-weight:600;margin-top:.25rem}
.estacao .sub{margin:.35rem 0 0;color:var(--tinta-fraca);font-size:.94rem}
.dia{position:relative;display:grid;grid-template-columns:1fr auto;gap:0 1.4rem;
align-items:start;padding:1.2rem 0;border-top:1px solid var(--linha)}
.marcador{position:absolute;left:calc(-1*clamp(2.7rem,7vw,4rem));top:1.35rem;
width:clamp(2.2rem,6vw,3rem);text-align:center}
.marcador .num{display:block;font:600 .93rem/1 var(--mono);font-variant-numeric:tabular-nums;
background:var(--papel);padding:.18rem 0}
.marcador .data{display:block;font:400 .67rem/1.4 var(--mono);color:var(--tinta-fraca)}
.dia h3{font-size:1.2rem;font-weight:600;display:flex;flex-wrap:wrap;align-items:center;gap:.55rem}
.dia p{margin:.45rem 0 0;color:var(--tinta-fraca);max-width:60ch;font-size:.98rem}
.custo{text-align:right;display:flex;flex-direction:column;gap:.12rem;font-family:var(--mono);
font-variant-numeric:tabular-nums;padding-top:.2rem;white-space:nowrap}
.custo .brl{font-weight:600;font-size:1rem;color:var(--ocre)}
.custo .cny,.custo .livre{font-size:.75rem;color:var(--tinta-fraca)}
.selo{font:600 .61rem/1 var(--mono);letter-spacing:.11em;text-transform:uppercase;padding:.33rem .5rem;border-radius:2px}
.estrela{background:var(--cinabrio);color:#fff}
.talvez{border:1px solid var(--linha);color:var(--tinta-fraca)}
.meio{border:1px solid var(--jade);color:var(--jade)}
.dia.destaque h3{font-size:1.34rem}
.dia.opcional .conteudo{opacity:.84}
.contas{margin-top:4rem;background:var(--superficie);border:1px solid var(--linha);
border-radius:4px;padding:clamp(1.4rem,4vw,2.2rem);box-shadow:var(--sombra)}
.contas h2{font-size:1.55rem;font-weight:600}
.contas>p{color:var(--tinta-fraca);margin:.55rem 0 1.6rem;max-width:56ch}
.rolagem{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:.95rem}
th{font:600 .67rem/1 var(--mono);letter-spacing:.12em;text-transform:uppercase;
color:var(--tinta-fraca);text-align:left;padding:0 0 .7rem;border-bottom:1px solid var(--linha)}
th.v,td.v{text-align:right;font-family:var(--mono);font-variant-numeric:tabular-nums;white-space:nowrap}
td{padding:.62rem 0;border-bottom:1px solid var(--linha)}
tfoot td{font-weight:700;border-top:2px solid var(--tinta);border-bottom:none;padding-top:.9rem}
.aviso{margin-top:2.2rem;border-left:3px solid var(--cinabrio);padding:.15rem 0 .15rem 1.15rem}
.aviso h3{font-size:1.02rem;font-weight:600}
.aviso p{margin:.42rem 0 0;color:var(--tinta-fraca);font-size:.93rem;max-width:58ch}
footer{margin-top:2.6rem;padding-top:1.3rem;border-top:1px solid var(--linha);
color:var(--tinta-fraca);font-size:.79rem;font-family:var(--mono);line-height:1.7}
@media (max-width:620px){.dia{grid-template-columns:1fr}
.custo{text-align:left;flex-direction:row;gap:.65rem;align-items:baseline;margin-top:.55rem}}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
"""

pagina = f"""<title>Vinte Dias na China</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600&family=Atkinson+Hyperlegible:wght@400;700&family=IBM+Plex+Mono:wght@400;600&display=swap">
<style>{css}</style>

<div class="envelope">
<header class="capa">
  <span class="olho">{periodo}</span>
  <h1>Vinte dias<br>na <em>China</em></h1>
  <p class="linha-fina">{T.CAPA_LINHA}</p>
  <dl class="fatos">
    <div class="fato"><dt>Quem vai</dt><dd>{VIAJANTES} pessoas</dd></div>
    <div class="fato"><dt>Cidades</dt><dd>{CIDADES_TOTAL}</dd></div>
    <div class="fato"><dt>Dias</dt><dd>{DIAS_TOTAL}</dd></div>
    <div class="fato"><dt>Passeios e comida</dt><dd>R$ {fmt(brl(passeios_cny))}</dd></div>
  </dl>
</header>

<section class="antes">
  <h2>Antes de embarcar</h2>
  <p class="antes-intro">{T.ANTES_INTRO}</p>
  {antes_blocos}
</section>

<main class="jornada">
{chr(10).join(blocos)}
</main>

<section class="contas">
  <h2>As contas</h2>
  <p>{T.CONTAS_INTRO.replace("o IOF incluído", f"o IOF de {IOF:.1%} incluído")}</p>
  <div class="rolagem">
  <table>
    <thead><tr><th>Item</th><th class="v">Em yuan</th><th class="v">Em reais</th></tr></thead>
    <tbody>
      <tr><td>Passeios, entradas e alimentação, {DIAS_TOTAL} dias</td><td class="v">&yen; {fmt(passeios_cny)}</td><td class="v">R$ {fmt(brl(passeios_cny))}</td></tr>
      {linhas_extras}
      <tr><td>eSIM Maya, {ESIM_LINHAS} celulares (cobrado em dólar)</td><td class="v">&mdash;</td><td class="v">R$ {fmt(ESIM_BRL)}</td></tr>
    </tbody>
    <tfoot><tr><td>Total já calculado</td><td class="v">&yen; {fmt(passeios_cny + transporte_cny)}</td><td class="v">R$ {fmt(total_brl)}</td></tr></tfoot>
  </table>
  </div>

  <div class="aviso">
    <h3>Ainda falta somar</h3>
    <p>{T.AVISO_FALTA}</p>
  </div>

  <div class="aviso">
    <h3>Uma coisa a confirmar</h3>
    <p>{T.AVISO_VISTO}</p>
  </div>
</section>

<section class="cuidados">
  <h2>Na rua</h2>
  <p class="antes-intro">{T.GOLPES_INTRO}</p>
  <div class="golpes">
    {golpes_blocos}
  </div>
  <p class="regra">{T.GOLPE_REGRA}</p>
  <p class="menor">{T.GOLPES_EXTRA}</p>
  <ul class="praticos">
      {praticos_itens}
  </ul>
  <div class="rolagem">
  <table class="fones">
    <thead><tr><th>Se algo der errado</th><th class="v">Telefone</th></tr></thead>
    <tbody>
      {emergencia_linhas}
    </tbody>
  </table>
  </div>
</section>

<footer>
  {T.RODAPE.format(taxa=TAXA, iof=f"{IOF:.1%}")}<br>
  Valor do eSIM estimado em US$ {ESIM_USD_POR_LINHA} por linha, a confirmar no aplicativo da Maya.
</footer>
</div>
"""

destino = RAIZ / "roteiro-china.html"
destino.write_text(pagina, encoding="utf-8")
print("escrito:", destino.stat().st_size, "bytes")
print(f"passeios R$ {brl(passeios_cny)} | transporte R$ {brl(transporte_cny)} | eSIM R$ {ESIM_BRL}")
print(f"total ja calculado: R$ {total_brl}")
