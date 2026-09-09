---
name: documentos-br
description: Diz o que o viajante brasileiro precisa para entrar num destino - visto, passaporte, vacina e seguro viagem - com a data do dado e o prazo para providenciar. Use sempre que a conversa envolver visto, passaporte, ETA, vacina, febre amarela, CIVP, seguro viagem, imigracao, "preciso de visto para", "o que preciso levar", ou documentos de viagem. Use tambem antes de fechar qualquer compra de passagem internacional, porque documento faltando e o unico erro que impede o embarque.
---

# Documentos para o passaporte brasileiro

Esta skill existe porque a ferramenta equivalente do trvl **responde errado** para
brasileiro: o dataset dela nao tem o Brasil como passaporte, entao toda consulta
cai no padrao e devolve `"visa-required"` - para Franca, Portugal, Japao, tudo.
Com `success: true`. Aqui a resposta vem de dado real, com carimbo de data.

## Visto: use o script

```bash
python .claude/skills/documentos-br/scripts/visto.py FR PT JP
python .claude/skills/documentos-br/scripts/visto.py --listar-sem-visto
```

O dado vem de `dados/passport-index/br.csv`, 199 destinos, e o script sempre
imprime a data do dado e a ressalva junto. Nao reproduza a resposta sem a data.

Se o dado estiver com mais de uns seis meses, rode
`python dados/passport-index/atualizar.py` antes de responder - ele mostra o que
mudou desde a ultima vez. Foi assim que apareceu que a China deixou de exigir
visto de brasileiro.

**A ressalva nao e formalidade.** O dataset e raspado do Passport Index, site
comercial, sem garantia oficial. Serve para orientar e para nao repetir o erro
grosseiro do trvl. Antes de comprar passagem, o usuario confirma no consulado.

## Vacina e seguro: ainda nao temos dado

`dados/vacina.json` e `dados/seguro.json` estao vazios de proposito. Procurei e
nao existe dataset publico confiavel para nenhum dos dois.

Entao **nao responda de memoria**. Para esses dois, busque na web, cite a fonte e
a data da consulta na resposta, e grave a entrada no JSON no formato que o
`modelo_de_entrada` mostra - assim a proxima viagem para o mesmo destino ja nasce
respondida. Fontes que valem: ANVISA para o CIVP, site oficial de saude do pais de
destino, e a norma do bloco para seguro (Schengen e o caso mais comum).

Febre amarela tem uma pegadinha de prazo: o certificado so vale 10 dias depois da
dose. Quem descobre isso uma semana antes de viajar nao viaja.

## Como responder

Organize por **prazo**, nao por tipo. Use o script, que ja faz o calendario
reverso a partir da data da viagem:

```bash
python .claude/skills/documentos-br/scripts/prazos.py 2027-01-15 --exige-visto --exige-civp
```

Passe as flags conforme o que a [[documentos-br]] apurou sobre o destino: se o
visto.py disse `eta`, use `--exige-eta`; se o destino exige certificado de vacina,
`--exige-civp`.

Um so prazo esta apurado hoje: a febre amarela, 10 dias, porque a validade do CIVP
so comeca 10 dias apos a dose - regra do Regulamento Sanitario Internacional, nao
recomendacao. Os demais aparecem na secao "prazo ainda nao apurado".

**Nao trate essa secao como rodape.** Ela e o risco real: sem saber quanto demora
o consulado, nao da para dizer se a viagem cabe na data. Ao responder, diga
explicitamente o que precisa ser descoberto e sugira onde - e, se o usuario
descobrir, registre em `dados/prazos.json` para a proxima viagem ja nascer certa.

Termine separando o que veio de dado datado do que veio de busca na web agora.
Ver [[dado-datado]].
