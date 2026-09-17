# Implementation Tasks

## Overview

Plano de execucao da conferencia de arquivos de viagem, em seis fases. A ordem e
ditada por uma dependencia dura: nada pode ser conferido antes de as tres
informacoes que hoje so existem em prosa virarem dado, entao o contrato de dados e a
Fase 1 e o resto vem depois dela.

As Fases 2 e 3 constroem o conferidor e suas checagens; a Fase 4 mexe no
`consolidar.py`, que e o unico ponto onde esta mudanca altera um numero que ja sai
hoje. A Fase 5 cobre os 37 criterios de aceite e a Fase 6 fecha.

## Repository Constraints

- Nenhum teste toca a rede. Cotacao e sobretaxa entram por parametro ou por arquivo de `dados/`, como a suite ja faz em `tests/test_viagens.py`.
- Regra de recusa e regra de silencio sao verificadas por mutacao: quebrar a regra tem de derrubar exatamente o teste correspondente.
- Arquivo de viagem e dado pessoal e fica fora do git. Todo teste que varre `viagens/` usa `glob` e tolera ausencia, nunca nomeia o arquivo da viagem real.
- `Path.write_text` no Windows converte o arquivo para CRLF e quebra o `sds`. Ao editar spec por script, passar `newline="\n"`.
- A formula de conversao e uma so, em `cambio.em_reais`. A sobretaxa entra na composicao existente, nunca numa copia.

## Discovery Evidence

- Target: `Levantar todo item de falta_organizar.reservar_com_antecedencia com janela de compra e confirmar se janela_dias cobre todos`
  - Result: 4 itens, e so **um** tem janela numerica. Ingresso de museu: `"exatamente 7 dias antes"`, `critico: true`. Trem-bala: `"a venda abre ~15 dias antes"`, aproximado. Hospedagem: `"a partir de outubro/2026"` e guia: `"algumas semanas antes"` sao janelas abertas, sem prazo fixo. `critico: true` aparece so nesse ingresso.
  - Plan impact: `janela_dias` e opcional, nao obrigatorio (tarefa 1.2), e as checagens de REQ-6 so se aplicam onde ele existe. Tarefa 3.4 trata janela ausente como nao conferivel, nao como erro.

- Target: `Varrer dados/*.json atras de outras regras de custo por destino que nao chegam ao total`
  - Result: so o `china-cuidados.json` tem regra de custo por destino, e ela aparece **duas vezes no mesmo arquivo**: `pagamentos.taxa_cross_border` (`"3% sobre transacao internacional no app"`) e `pagamentos.app.taxa` (`{"abaixo_de_200_cny": "0%", "acima": "3%"}`). O `iof.json` tem aliquotas, mas sao nacionais e ja consumidas pelo `cambio.py`.
  - Plan impact: DES-6 atende so a sobretaxa, nao uma familia maior. A tarefa 1.3 canoniza a duplicata em vez de so acrescentar campo, senao a mudanca cria a terceira copia da mesma regra.

- Target: `Confirmar como roteiro[].dias se comporta em bloco de deslocamento`
  - Result: bloco de `trecho` nao tem `noites` e usa dia unico (`"8"`, `"11"`, `"14"`, `"20"`) ou intervalo (`"1-2"`). A sobreposicao com a cidade vizinha e **inconsistente**: o dia 8 e compartilhado com a primeira cidade (`"2-8"`), o dia 11 com a terceira (`"11-13"`), e o dia 14 nao pertence a cidade nenhuma.
  - Plan impact: confirma DES-3 — `noites` e a fonte e `dias` e prosa. E obriga a tarefa 3.3: REQ-2.3 nao pode acusar sobreposicao entre um trecho e a cidade vizinha, que e o normal de um dia de viagem; so sobreposicao entre dois blocos de cidade e conflito.

- Target: `Confirmar que o exemplo de Lisboa nao muda de total com DES-6`
  - Result: destino e `PT`; o unico arquivo de cuidados e o da China e ele nao tem campo `pais`. Nenhuma sobretaxa alcanca Lisboa. Alem disso, a premissa do design estava **errada**: nenhum teste fixa o total. O valor R$ 25.696,81 aparece so na prosa do `BACKLOG.md`, e rodando hoje o exemplo da R$ 25.436,43, porque o euro se moveu.
  - Plan impact: risco de regressao menor que o previsto. A tarefa 4.3 verifica que Lisboa nao ganha sobretaxa, e nao tenta preservar um total absoluto, que e movel por natureza.

## Phase 1: Contrato de dados

- [x] 1.1 Add `datas_bloqueadas[]` ao esquema de viagem
  - Definir data em ISO-8601, razao e a decisao de origem, e documentar no `viagens/_esquema.md` que decisao continua em prosa e o campo novo e o recorte conferivel dela.
  - _Implements: DES-1, REQ-2.1_

- [x] 1.2 Add `janela_dias` e `critico` opcionais ao esquema de viagem
  - Documentar que so item com prazo fixo declara `janela_dias`, que janela aberta fica sem o campo, e que `critico` marca item sem segunda chance.
  - _Depends: 1.1_
  - _Implements: DES-1_

- [x] 1.3 Update `dados/china-cuidados.json` com `pais` e sobretaxa numerica
  - Acrescentar `pais` em ISO-2 e `valor` numerico, e canonizar as duas declaracoes da mesma taxa de 3% numa so, deixando a prosa como descricao e nao como fonte.
  - _Implements: DES-1_

- [x] 1.4 Test: toda data bloqueada nomeia a decisao de origem
  - Verificar que uma entrada de `datas_bloqueadas[]` sem decisao e recusada, e que uma com decisao passa.
  - Test type: unit
  - _Depends: 1.1_
  - _Implements: REQ-2.1_

- [x] 1.6 Update `viagens/exemplo-lisboa-2027-03.json` com o contrato novo
  - Acrescentar `datas_bloqueadas[]` e um item com `janela_dias` ao exemplo publico, para o esquema ter demonstracao e a conferencia ter dado real onde morder. Sem isso a tarefa 1.4 passa vazia, e viagem real fica fora do git.
  - _Discovered from: 1.4_
  - _Implements: DES-1, REQ-2.1_

- [x] 1.5 Test: dados de destino declaram pais e uma so fonte numerica
  - Verificar que o arquivo de cuidados declara `pais` em ISO-2 e `valor` numerico, e que a taxa de 3% aparece uma unica vez como fonte, nao duas.
  - Test type: unit
  - _Depends: 1.3_
  - _Implements: REQ-4.1_

- [x] 1.7 Add `roteiro[]` ao esquema de viagem
  - O campo existe no arquivo de viagem real com 9 blocos e sustenta DES-3 e DES-4 inteiros, mas nunca foi definido no esquema: aparece so em prosa. Documentar bloco de cidade (`cidade`, `dias`, `noites`) e bloco de deslocamento (`trecho`, `dias`, sem noites), e registrar que `dias` localiza e `noites` conta.
  - _Discovered from: 2.2_
  - _Implements: DES-1, REQ-1.1_

- [x] 1.8 Update o exemplo de Lisboa com um `roteiro[]`
  - Sem roteiro, `data_de_visita` devolve None e as checagens de REQ-1 e REQ-6 nao tem onde morder no unico arquivo de viagem que existe num clone limpo.
  - _Depends: 1.7_
  - _Discovered from: 2.2_
  - _Implements: DES-1, REQ-6.1_

## Phase 2: Conferidor e calendario derivado

- [x] 2.1 Create `conferir.py` com varredura de `viagens/`
  - Entrada na raiz, irmao do `saude.py`: aceita caminho opcional, varre `viagens/*.json` sem argumento, abre arquivo apenas para leitura.
  - _Depends: 1.1_
  - _Implements: DES-2, REQ-7.3, REQ-8.1, REQ-8.3_

- [x] 2.2 Add derivacao de datas a partir de `datas.ida`
  - Dia 1 e a ida, dia N e `ida + N - 1`. `noites` e a fonte para contar; `dias` nao entra em conta.
  - _Depends: 2.1_
  - _Implements: DES-3, REQ-1.1, REQ-6.1_

- [x] 2.3 Add calendario por hipotese quando o pouso nao esta confirmado
  - Enquanto a passagem nao estiver comprada, derivar um calendario por data de pouso possivel e exibir todas, sem eleger uma.
  - _Depends: 2.2_
  - _Implements: DES-3, REQ-1.3_

- [x] 2.4 Add relatorio na saida padrao e codigo de saida
  - Agrupar divergencias por familia, imprimir o caminho de cada arquivo conferido, e sair zero sem divergencia e diferente de zero com. Quando a correcao for obvia, descreve-la no relatorio como texto e nunca aplica-la.
  - _Depends: 2.1_
  - _Implements: DES-7, REQ-7.1, REQ-7.2, REQ-8.2_

- [x] 2.5 Add recusa de saida em arquivo
  - Rejeitar pedido de relatorio em arquivo, explicando que ele carrega dado pessoal de viagem que o `.gitignore` mantem fora do repositorio.
  - _Depends: 2.4_
  - _Implements: DES-7, REQ-8.4, REQ-8.5_

- [x] 2.6 Add tratamento de arquivo ausente, ilegivel e diretorio vazio
  - Registrar o motivo e encerrar diferente de zero em cada caso, sem confundir "nao existe" com "nada a conferir".
  - _Depends: 2.1_
  - _Implements: DES-2, REQ-7.4, REQ-7.5_

- [x] 2.7 Update `.claude/skills/viagem/SKILL.md` com o passo de conferencia
  - Citar `conferir.py` no fluxo da skill, antes de fechar custo. Capacidade que a skill nao menciona nao e chamada, e o risco central destas skills e subdisparo.
  - _Depends: 2.4_
  - _Implements: DES-2_

- [x] 2.8 Test: varredura, codigo de saida e somente leitura
  - Verificar que o conferidor varre o diretorio, encerra com o codigo certo nos dois casos e deixa o arquivo byte a byte igual.
  - Test type: integration
  - _Depends: 2.4_
  - _Implements: REQ-7.1, REQ-8.1_

## Phase 3: Checagens de calendario e de orcamento

- [x] 3.1 Add checagem de noites contra o intervalo da viagem
  - Comparar a soma de `roteiro[].noites` com as noites que o intervalo entre ida e volta comporta, e registrar os dois numeros e a diferenca.
  - _Depends: 2.2_
  - _Implements: DES-4, REQ-1.2_

- [x] 3.11 Add `noites` opcional a linha de custo de hospedagem
  - REQ-1.4 confere o numero de noites que a linha declara, e REQ-1.5 trata a ausencia dele, mas o esquema nao tem esse campo: hoje a contagem vive no texto do item (`"Hospedagem, 9 noites"`). Ler dali seria parse de prosa, que e o defeito que esta mudanca existe para eliminar. Documentar no esquema e usar no exemplo.
  - _Discovered from: 3.2_
  - _Implements: DES-1, REQ-1.4_

- [x] 3.2 Add checagem da hospedagem contra a soma do roteiro
  - Onde a linha de hospedagem declarar numero de noites, registrar a divergencia; onde nao declarar, registrar que ela nao pode ser conferida.
  - _Depends: 3.1_
  - _Implements: DES-4, REQ-1.4, REQ-1.5_

- [x] 3.3 Add checagem de deslocamento contra data bloqueada
  - Acusar trecho que cai em data bloqueada, nomeando a decisao, e acusar bloqueio sem procedencia. Sobreposicao entre trecho e cidade vizinha e o normal de um dia de viagem e nao vira conflito; so sobreposicao entre dois blocos de cidade vira.
  - _Depends: 2.2_
  - _Implements: DES-4, REQ-2.2, REQ-2.3, REQ-2.4_

- [x] 3.4 Add checagem de decisao que nao virou dado conferivel
  - Acusar decisao cujo texto contem uma data sem entrada correspondente em `datas_bloqueadas[]`.
  - _Depends: 3.3_
  - _Implements: DES-4, REQ-2.5_

- [x] 3.5 Add checagem de data de compra contra a data de visita
  - Derivar a data de compra de `janela_dias` e da data de visita, acusar divergencia com a data declarada, e acusar item critico sem data de visita ou em dia restrito. Item sem `janela_dias` fica fora, nao vira erro.
  - _Depends: 2.2_
  - _Implements: DES-4, REQ-6.2, REQ-6.3, REQ-6.4_

- [x] 3.12 Add `orcamento.cotacoes` como fonte offline de taxa
  - DES-5 manda calcular a faixa sem rede, usando a cotacao registrada no arquivo. Existe `orcamento.cotacao_cny_brl`, mas o nome fixa uma moeda so e a viagem tem CNY e USD. Generalizar para um mapa `moeda -> BRL por unidade`, com a data em que foi registrada.
  - _Discovered from: 3.6_
  - _Implements: DES-5, REQ-3.1_

- [x] 3.6 Add faixa de orcamento calculada a partir de `custos[]`
  - Somar linhas com preco, estimativas em faixa numerica e a folga; comparar com a faixa declarada e registrar a diferenca e o estouro no piso.
  - _Depends: 2.1_
  - _Implements: DES-5, REQ-3.1, REQ-3.2, REQ-3.3, REQ-3.4_

- [x] 3.7 Add recusa por linha na faixa
  - Deixar de fora e nomear a linha sem estimativa, a estimativa sem minimo e maximo, e a linha em moeda estrangeira sem cotacao registrada, dizendo quanto da faixa ficou coberto.
  - _Depends: 3.6_
  - _Implements: DES-5, REQ-3.5, REQ-3.6_

- [x] 3.8 Add checagem de custo fora de `custos[]`
  - Acusar valor de custo em qualquer outro campo e acusar `custos[]` vazio.
  - _Depends: 3.6_
  - _Implements: DES-5, REQ-3.7, REQ-3.8_

- [x] 3.9 Add checagem de sobretaxa registrada e ausente do orcamento
  - Acusar sobretaxa que existe nos dados do destino e nao aparece em nenhuma linha, com o valor que ela acrescenta, nomeando o arquivo de dados de origem.
  - _Depends: 1.3, 3.6_
  - _Implements: DES-5, REQ-5.1, REQ-5.2_

- [x] 3.10 Test: fumaca das tres familias construidas nesta fase
  - Um caso que acusa e um contraprovado silencioso para calendario, orcamento e sobretaxa ausente, so para pegar quebra cedo. A cobertura criterio a criterio e da Fase 5, nao daqui.
  - Test type: unit
  - _Depends: 3.9_
  - _Implements: REQ-1.2, REQ-2.2, REQ-3.1_

## Phase 4: Sobretaxa no consolidador

- [x] 4.1 Add busca de sobretaxa por pais em `consolidar.py`
  - Procurar nos arquivos de `dados/` um registro cujo `pais` case com `destino.pais` e aplicar `sobretaxa.valor` as linhas em moeda estrangeira, pela composicao de `cambio.em_reais`.
  - _Depends: 1.3_
  - _Implements: DES-6, REQ-4.1_

- [x] 4.2 Add exibicao da carga separada por componente
  - Mostrar IOF, spread e sobretaxa em separado por linha em moeda estrangeira, e registrar sobretaxa ou isencao cuja validade termina antes da ida como fora de alcance, com a data.
  - _Depends: 4.1_
  - _Implements: DES-6, REQ-4.2, REQ-4.3_

- [x] 4.4 Update a checagem de REQ-5 para o que o consolidador nao alcanca
  - Com a Fase 4, o `consolidar.py` aplica a sobretaxa do destino sozinho, a partir de `dados/`. A checagem de REQ-5 foi escrita supondo que ela precisaria de uma linha de custo manual, e continuaria acusando "fora do orcamento" algo que agora esta dentro - para sempre, sem acao possivel. Estreitar para o caso real: sobretaxa registrada que nao acha nenhuma linha na `moeda_local` onde incidir.
  - _Discovered from: 4.1_
  - _Implements: DES-5, REQ-5.1_

- [x] 4.3 Test: sobretaxa aplicada na China e ausente em Portugal
  - Verificar que o destino com sobretaxa registrada tem o total acrescido e a carga separada, e que o exemplo de Lisboa nao ganha sobretaxa alguma. Nao fixar total absoluto: ele se move com a cotacao.
  - Test type: integration
  - _Depends: 4.2_
  - _Implements: REQ-4.1, REQ-4.2_

## Phase 5: Acceptance Criteria Testing

- [x] 5.1 Test: noites do roteiro contra o intervalo, com pouso confirmado e sem
  - Verificar a comparacao, a divergencia relatada e as multiplas contagens quando a data de pouso ainda admite mais de um valor.
  - Test type: unit
  - _Depends: 3.1_
  - _Implements: REQ-1.1, REQ-1.2, REQ-1.3_

- [x] 5.2 Test: hospedagem com e sem numero de noites declarado
  - Test type: unit
  - _Depends: 3.2_
  - _Implements: REQ-1.4, REQ-1.5_

- [x] 5.3 Test: deslocamento em data bloqueada e bloqueio sem procedencia
  - Test type: unit
  - _Depends: 3.3_
  - _Implements: REQ-2.1, REQ-2.2, REQ-2.4_

- [x] 5.4 Test: sobreposicao de cidades e decisao que nao virou dado
  - Verificar que dois blocos de cidade no mesmo dia acusam, que trecho sobre cidade vizinha nao acusa, e que decisao com data sem par e relatada.
  - Test type: unit
  - _Depends: 3.4_
  - _Implements: REQ-2.3, REQ-2.5_

- [x] 5.5 Test: faixa calculada contra faixa declarada
  - Verificar a soma das linhas, a inclusao da folga, a diferenca relatada e o estouro no piso.
  - Test type: unit
  - _Depends: 3.6_
  - _Implements: REQ-3.1, REQ-3.2, REQ-3.3, REQ-3.4_

- [x] 5.6 Test: recusas por linha nao derrubam a faixa inteira
  - Test type: unit
  - _Depends: 3.7_
  - _Implements: REQ-3.5, REQ-3.6_

- [x] 5.7 Test: custo fora de `custos[]` e `custos[]` vazio
  - Test type: unit
  - _Depends: 3.8_
  - _Implements: REQ-3.7, REQ-3.8_

- [x] 5.8 Test: sobretaxa aplicada, carga separada e validade vencida
  - Test type: integration
  - _Depends: 4.2_
  - _Implements: REQ-4.1, REQ-4.2, REQ-4.3_

- [x] 5.9 Test: sobretaxa registrada nos dados e ausente do orcamento
  - Verificar tambem que o relatorio nomeia o arquivo de dados de origem.
  - Test type: unit
  - _Depends: 3.9_
  - _Implements: REQ-5.1, REQ-5.2_

- [x] 5.10 Test: data de compra derivada e divergente da declarada
  - Test type: unit
  - _Depends: 3.5_
  - _Implements: REQ-6.1, REQ-6.2_

- [x] 5.11 Test: item critico em dia restrito e sem data de visita
  - Test type: unit
  - _Depends: 3.5_
  - _Implements: REQ-6.3, REQ-6.4_

- [x] 5.12 Test: codigo de saida com e sem divergencia
  - Test type: integration
  - _Depends: 2.4_
  - _Implements: REQ-7.1, REQ-7.2_

- [x] 5.13 Test: relatorio nomeia campo, valores e caminho, e falha ao ler
  - Verificar o conteudo do relatorio, o caminho de cada arquivo conferido, o arquivo ilegivel e o diretorio sem viagem alguma.
  - Test type: integration
  - _Depends: 2.6_
  - _Implements: REQ-7.3, REQ-7.4, REQ-7.5, REQ-8.3_

- [x] 5.14 Test: somente leitura e recusa de saida em arquivo
  - Verificar que o arquivo continua byte a byte igual mesmo quando o conferidor sabe a correcao, que o relatorio so vai para a saida padrao e que o pedido de arquivo e recusado.
  - Test type: integration
  - _Depends: 2.5_
  - _Implements: REQ-8.1, REQ-8.2, REQ-8.4, REQ-8.5_

- [x] 5.15 Test: mutacao derruba a regra correspondente
  - Quebrar cada regra de recusa e de silencio e confirmar que cada uma derruba exatamente o seu teste, como a suite ja faz.
  - Test type: unit
  - _Depends: 5.14_
  - _Implements: REQ-3.5, REQ-8.4_

## Phase 6: Final Checkpoint

- [x] 6.1 Verificacao final da mudanca
  - Rodar a suite completa, rodar `python conferir.py` e `python saude.py` no repositorio, confirmar que o `viagens/exemplo-lisboa-2027-03.json` continua valido no esquema novo, e registrar os achados restantes no `BACKLOG.md`.
  - _Implements: All requirements_
