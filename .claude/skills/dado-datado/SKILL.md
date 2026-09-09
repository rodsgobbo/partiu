---
name: dado-datado
description: Disciplina para lidar com dado que estraga - aliquota de imposto, exigencia de visto, cobertura de seguro, tabela de vacina. Use sempre que for gravar, ler ou afirmar um numero ou uma regra que muda com o tempo, e sempre que for escrever qualquer skill deste projeto. Tambem use quando alguem perguntar "isso ainda vale?", "de onde veio esse numero?" ou quando um calculo depender de aliquota, taxa ou regra oficial.
---

# Dado datado

Este projeto responde perguntas onde errar custa dinheiro ou embarque negado. O
risco maior nao e nao saber - e **afirmar com confianca um dado vencido**.

Dois casos reais que motivaram esta skill:

- O `check_visa` do trvl devolve `"visa-required"` para todo destino quando o
  passaporte e brasileiro, porque o Brasil nao esta no dataset dele. Ele responde
  `success: true`. Um "nao sei" honesto teria sido melhor que a resposta errada.
- O dataset de vistos mais estrelado do GitHub tem commit de fevereiro de 2026,
  mas o dado esta congelado em janeiro de 2025. O `pushed_at` era so um README
  editado. Quem confia na data do repositorio erra em 13 destinos.

## As regras

**Todo dado perecivel mora em `dados/`, em JSON, nunca no meio do codigo nem no
texto de uma skill.** Numero solto dentro de script nao tem como ser auditado nem
atualizado sem alguem reler o codigo.

**Toda entrada carrega quatro campos**, com estes nomes exatos:

```json
{
  "valor": 0.035,
  "verificado": false,
  "fonte": "https://...",
  "consultado_em": "2026-08-27"
}
```

Os nomes sao fixos porque a disciplina so vale se der para checar por script.
Este projeto ja teve tres nomes para a mesma coisa - `consultado_em`,
`baixado_em`, `data_da_coleta` - e enquanto foi assim nenhum teste conseguia
cobrar o campo de ninguem. Hoje `tests/test_viagens.py` roda a conformidade em
todo JSON de `dados/` e falha se um nome antigo voltar.

`data_do_dado` pode existir ao lado, e e outro conceito: a data da fonte la em
cima, nao a data em que voce olhou. As duas importam e nao se substituem - foi
por confundir as duas que um dataset com commit de fevereiro de 2026 escondia
dado de janeiro de 2025.

**Quando `verificado` for false, diga o que falta** num campo `pendencia`. Marcar
falso sem explicar deixa a pendencia invisivel: ninguem sabe o que fazer para
fechar, e o arquivo fica parado.

`verificado: true` significa uma coisa so: **alguem leu a fonte primaria** - o
decreto, o site do consulado, a norma. Blog, casa de cambio e agregador sao pista
para achar a fonte, nao sao a fonte.

**Quando `verificado` for false, diga isso na resposta.** Nao no rodape, nao em
letra miuda: junto do numero. O `cambio.py` faz assim - marca a linha com `*` e
explica embaixo o que o asterisco quer dizer.

**Quando as fontes se contradizem, grave `null` e registre o conflito.** Escolher
uma das duas por conta propria e inventar precisao. O `iof.json` guarda o conflito
sobre a aliquota de especie em vez de chutar.

**Toda resposta que usa dado de `dados/` mostra a data do dado.** Quem le decide
se seis meses e aceitavel para aquela pergunta. Sem a data, nao da para decidir.

## Ao escrever uma skill nova aqui

Pergunte: o que nela vira mentira em seis meses? Isso sai do texto da skill e vai
para `dados/`, com os quatro campos. O que sobra no SKILL.md e o metodo, que
envelhece devagar.

Se o dado tem uma fonte que da para reprocessar, escreva o script de atualizacao
junto - veja `dados/passport-index/atualizar.py`. Ele rebaixa a fonte, regrava o
carimbo e **mostra o que mudou desde a ultima vez**. E o diff que revela que a
China deixou de exigir visto, nao o arquivo novo em si.
