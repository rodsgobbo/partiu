# Requirements

## Overview

A validacao da primeira viagem real, feita em 09/09/2026, encontrou cinco defeitos
no arquivo dessa viagem. Todos tem a mesma forma: uma contradicao entre
dois blocos do mesmo arquivo. Duas decisoes moveram um trem e um passeio
para fugir de um feriado, e o bloco `roteiro` continuou na data antiga. A faixa de
orcamento declarada a mao deixou de fora uma linha de custo do proprio arquivo. As
noites somadas nao fecham com as datas de ida e volta. A sobretaxa de pagamento do
destino estava registrada nos dados do projeto e nunca chegou ao total. A data de
compra de um ingresso critico foi fixada a mao em vez de sair da data da visita.

Nenhum deles e erro de conta, e nenhum foi encontrado por ferramenta: todos
apareceram porque uma pessoa leu os dois lados e reparou. O projeto ja tem esse
controle para os arquivos de `dados/` — o `saude.py` le a data e a validade de
cada dado e falha quando algo venceu — e nao tem nada equivalente para os arquivos
de `viagens/`, que sao justamente onde as decisoes caras moram.

Os achados estao registrados no `BACKLOG.md` como item 3.1-a. Cada requisito abaixo
fecha um deles: REQ-1 as noites, REQ-2 o
roteiro contra as decisoes registradas, REQ-3 a faixa de orcamento que excluiu a folga,
REQ-4 e REQ-5 a sobretaxa de pagamento, REQ-6 a data de compra do ingresso. REQ-7 e
REQ-8 sao a moldura que faz a conferencia rodar sozinha sem estragar o arquivo.

O escopo desta mudanca e conferir e relatar. Corrigir o arquivo continua sendo
decisao de quem planeja a viagem: uma ferramenta que reescrevesse o roteiro sozinha
apagaria a razao registrada na decisao, que e a parte que custou mais caro.

## Glossary

| Termo | Definicao |
|------|------------|
| Arquivo de viagem | O JSON de uma viagem real em `viagens/`, no formato de `viagens/_esquema.md` |
| Linha de custo | Uma entrada de `custos[]`, com valor, moeda e se multiplica por viajante |
| Linha sem preco | Linha de custo com `valor` nulo: conhecida, ainda nao orcada |
| Data bloqueada | Data que o arquivo de viagem declara indisponivel, com a razao que a bloqueou |
| Janela de compra | Prazo fixo em que um item so pode ser comprado, contado da data da visita |
| Sobretaxa de pagamento | Taxa que o destino cobra sobre pagamento estrangeiro, alem de IOF e spread |
| Folga | Linha de custo reservada para imprevisto, em reais |

## Assumptions

- Os arquivos de viagem seguem `viagens/_esquema.md` na versao corrigida em 09/09/2026, em que todo custo mora em `custos[]` e `valor` nulo significa conhecido e nao orcado.
- Arquivos de viagem sao dado pessoal e ficam fora do git, entao a conferencia roda sobre o disco local e nunca depende de um arquivo versionado.
- A conferencia nao acessa a rede: cotacao e sobretaxa entram pelos arquivos de `dados/`, para a conferencia falhar por inconsistencia e nunca por internet fora do ar.

## Requirements

### REQ-1: Noites do roteiro reconciliam com as datas da viagem

**User Story:** As a planejador da viagem, I want que as noites somadas do roteiro sejam conferidas contra as datas de ida e volta, so that eu nao reserve uma noite a menos e descubra isso no balcao do hotel.

#### Acceptance Criteria
1.1 WHEN o conferidor de viagem le um arquivo de viagem, THEN the conferidor de viagem SHALL comparar a soma das noites declaradas no roteiro com o numero de noites que o intervalo entre ida e volta comporta.
1.2 IF a soma das noites do roteiro difere do numero de noites do intervalo, THEN the conferidor de viagem SHALL registrar os dois numeros e a diferenca entre eles.
1.3 WHERE a data de chegada depende de um deslocamento sem horario confirmado, the conferidor de viagem SHALL exibir todas as contagens de noites compativeis em vez de eleger uma.
1.4 WHERE uma linha de custo de hospedagem declara numero de noites, the conferidor de viagem SHALL registrar a divergencia entre esse numero e a soma das noites do roteiro.
1.5 IF uma linha de custo de hospedagem nao declara numero de noites, THEN the conferidor de viagem SHALL registrar que a hospedagem nao pode ser conferida contra o roteiro.

### REQ-2: Deslocamento nao cai em data que uma decisao bloqueou

**User Story:** As a planejador da viagem, I want que o roteiro seja conferido contra as datas que minhas proprias decisoes bloquearam, so that uma decisao tomada semanas atras nao fique valendo so no papel.

#### Acceptance Criteria
2.1 THE conferidor de viagem SHALL exigir que toda data declarada como bloqueada no arquivo de viagem nomeie a decisao que a bloqueou.
2.2 WHEN um trecho de deslocamento do roteiro cai numa data bloqueada, THEN the conferidor de viagem SHALL registrar o trecho, a data e a decisao que a bloqueou.
2.3 WHEN duas entradas do roteiro ocupam a mesma data com atividades diferentes, THEN the conferidor de viagem SHALL registrar as duas entradas e a data em conflito.
2.4 IF uma data bloqueada nao nomeia a decisao de origem, THEN the conferidor de viagem SHALL registrar a data como bloqueio sem procedencia.
2.5 IF uma decisao registrada contem uma data e nenhuma data bloqueada do arquivo corresponde a ela, THEN the conferidor de viagem SHALL registrar que a decisao nao foi convertida em dado conferivel.

### REQ-3: A faixa de orcamento vem das linhas de custo

**User Story:** As a planejador da viagem, I want que a faixa de custo total seja calculada a partir das linhas de custo, so that eu nao leve para quem viaja comigo um numero escrito a mao que deixou uma linha de fora.

#### Acceptance Criteria
3.1 THE conferidor de viagem SHALL calcular a faixa de custo total somando toda linha de custo com preco e as estimativas declaradas nas linhas sem preco.
3.2 THE conferidor de viagem SHALL incluir a folga para imprevisto na faixa calculada.
3.3 IF o arquivo de viagem declara uma faixa de orcamento propria, THEN the conferidor de viagem SHALL comparar essa faixa com a calculada e registrar a diferenca em reais.
3.4 IF a faixa calculada tem piso acima do orcamento informado, THEN the conferidor de viagem SHALL registrar o valor do estouro no piso.
3.5 IF uma linha sem preco nao declara estimativa, THEN the conferidor de viagem SHALL registrar que a faixa calculada esta incompleta e nomear a linha.
3.6 IF a estimativa de uma linha sem preco nao expressa um valor minimo e um maximo, THEN the conferidor de viagem SHALL registrar que a estimativa nao entra na faixa calculada e nomear a linha.
3.7 IF o arquivo de viagem declara valor de custo fora de `custos[]`, THEN the conferidor de viagem SHALL registrar o campo e o valor encontrado.
3.8 IF `custos[]` esta vazio, THEN the conferidor de viagem SHALL registrar que o arquivo nao tem custo algum a somar.

### REQ-4: Sobretaxa de pagamento do destino entra no total

**User Story:** As a viajante, I want que a sobretaxa que o destino cobra sobre pagamento estrangeiro entre no total, so that o numero que eu uso para decidir nao esteja abaixo do que vou pagar.

#### Acceptance Criteria
4.1 WHERE os dados do projeto registram sobretaxa de pagamento para o pais de destino, the consolidador SHALL aplicar essa sobretaxa a toda linha de custo em moeda estrangeira.
4.2 THE consolidador SHALL exibir a carga aplicada a cada linha em moeda estrangeira, separando IOF, spread e sobretaxa.
4.3 IF uma sobretaxa ou sua isencao tem validade que termina antes da data de ida, THEN the consolidador SHALL registrar que a regra nao alcanca a viagem e exibir a data de validade.

### REQ-5: Sobretaxa registrada nos dados chega ao arquivo de viagem

**User Story:** As a planejador da viagem, I want ser avisado quando uma regra de custo ja registrada nos dados do projeto nao aparece no orcamento da viagem, so that o dado que eu levantei uma vez nao fique parado num arquivo que ninguem soma.

#### Acceptance Criteria
5.1 IF os dados do projeto registram sobretaxa de pagamento para o pais de destino e nenhuma linha de custo do arquivo de viagem a reflete, THEN the conferidor de viagem SHALL registrar a sobretaxa ausente e o valor que ela acrescenta ao total.
5.2 THE conferidor de viagem SHALL nomear o arquivo de dados de origem de cada regra de custo que cobrar.

### REQ-6: Data de compra sai da data da visita

**User Story:** As a planejador da viagem, I want que a data de compra de um item com janela fixa seja derivada da data da visita no roteiro, so that mudar o roteiro nao me faca perder um ingresso que nao tem segunda chance.

#### Acceptance Criteria
6.1 THE conferidor de viagem SHALL derivar a data de compra de cada item com janela de compra a partir da data de visita registrada no roteiro e do tamanho da janela.
6.2 IF um item com janela de compra declara data de compra fixa que difere da data derivada, THEN the conferidor de viagem SHALL registrar as duas datas e o item afetado.
6.3 WHEN a data de visita de um item marcado como critico cai em dia de semana que o arquivo declara restrito para aquele item, THEN the conferidor de viagem SHALL registrar a restricao junto do item.
6.4 IF um item marcado como critico nao tem data de visita no roteiro, THEN the conferidor de viagem SHALL registrar que a data de compra dele nao pode ser derivada.

### REQ-7: O relatorio serve a hook e a integracao continua

**User Story:** As a planejador da viagem, I want que a conferencia falhe com codigo de saida quando achar divergencia, so that ela possa rodar sozinha e nao dependa de eu lembrar de ler o relatorio.

#### Acceptance Criteria
7.1 WHEN a conferencia termina sem divergencia, THEN the conferidor de viagem SHALL encerrar com codigo de saida zero.
7.2 IF a conferencia encontra ao menos uma divergencia, THEN the conferidor de viagem SHALL encerrar com codigo de saida diferente de zero.
7.3 THE conferidor de viagem SHALL exibir, para cada divergencia, o campo de origem no arquivo e os valores em conflito.
7.4 IF o arquivo de viagem nao existe ou nao pode ser lido, THEN the conferidor de viagem SHALL registrar o motivo e encerrar com codigo de saida diferente de zero.
7.5 IF nenhum arquivo de viagem existe no diretorio conferido, THEN the conferidor de viagem SHALL registrar que nada foi conferido e encerrar com codigo de saida diferente de zero.

### REQ-8: A conferencia nao altera o arquivo de viagem

**User Story:** As a planejador da viagem, I want que a conferencia so leia e relate, so that a razao que eu registrei numa decisao nao seja apagada por uma correcao automatica.

#### Acceptance Criteria
8.1 THE conferidor de viagem SHALL preservar o arquivo de viagem byte a byte durante toda a conferencia.
8.2 WHEN o conferidor de viagem encontra uma divergencia que sabe corrigir, THEN the conferidor de viagem SHALL descrever a correcao no relatorio e preservar o arquivo inalterado.
8.3 THE conferidor de viagem SHALL registrar o caminho de cada arquivo conferido no relatorio.
8.4 THE conferidor de viagem SHALL escrever o relatorio apenas na saida padrao.
8.5 IF o conferidor de viagem recebe um caminho de saida em arquivo, THEN the conferidor de viagem SHALL rejeitar o pedido e registrar que o relatorio contem dado pessoal de viagem.
