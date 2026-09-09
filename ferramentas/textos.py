# -*- coding: utf-8 -*-
"""Textos da pagina, com acentuacao correta. Separados do gerador porque quem
vai reler e ajustar isso e quem viaja, nao o codigo.

Conteudo de exemplo: um roteiro de 20 dias pela China, que serve de modelo para
escrever o seu. O gerador nao le nada daqui alem desta estrutura."""

DIAS = [
 ("voo", "Voo para a China",
  "São mais de 30 horas de avião, com uma escala no meio. Leve fone, livro e paciência: quando o avião pousar, o relógio já vai estar 11 horas na frente do de São Paulo.", 0, "voo"),
 ("Pequim", "Chegada em Pequim",
  "Pegar o hotel, tomar banho e comer alguma coisa por perto. O corpo vai achar que é madrugada mesmo sendo de tarde — dormir cedo hoje resolve o resto da viagem.", 400, None),
 ("Pequim", "Cidade Proibida",
  "O maior palácio do mundo: 980 prédios dentro de uma muralha só. Durante quase 500 anos, nenhuma pessoa comum podia entrar — daí o nome. No fim da tarde subimos a colina Jingshan, logo atrás, para ver o palácio inteiro de cima no pôr do sol.", 700, None),
 ("Pequim", "Templo do Céu e os hutongs",
  "De manhã, o templo onde o imperador rezava pedindo boa colheita. À tarde, os hutongs: becos estreitos de casas antigas onde as pessoas ainda moram hoje. À noite, pato laqueado, o prato mais famoso da cidade.", 950, None),
 ("Pequim", "A Muralha da China",
  "Trecho de Mutianyu, a uma hora de Pequim — mais bonito e bem menos cheio que o famoso Badaling. A muralha inteira tem mais de 21 mil quilômetros. Sobe-se de teleférico e desce-se de tobogã, num trilho de metal que serpenteia morro abaixo.", 1500, "destaque"),
 ("Pequim", "Festival do Meio-Outono",
  "Hoje é um dos feriados mais importantes da China, e por sorte estaremos em Pequim. As famílias se reúnem para olhar a lua cheia e comer bolo da lua — um docinho redondo recheado, que tem até versão com gema de ovo dentro. Os parques ficam cheios de lanternas acesas. Dia de andar sem pressa e ver a cidade em festa.", 600, "destaque"),
 ("Pequim", "Palácio de Verão",
  "O lugar para onde a família do imperador fugia do calor. Tem um lago enorme e um barco inteiro feito de mármore que, claro, nunca navegou: foi construído só para enfeitar.", 700, None),
 ("Pequim", "Bairro 798 e mercado",
  "O 798 era uma fábrica de armas e virou um bairro inteiro de arte moderna, com esculturas gigantes no meio da rua. Depois, o mercado de Panjiayuan, bom para garimpar lembrança.", 700, None),
 ("Xi'an", "Trem-bala para Xi'an",
  "Cinco horas e meia a mais de 300 km/h, em primeira classe. Xi'an já foi a capital da China por mais de mil anos, muito antes de Pequim existir. À noite, o Bairro Muçulmano: uma rua inteira de comida.", 600, "trem"),
 ("Xi'an", "Muralha de bicicleta",
  "Xi'an tem uma muralha própria em volta do centro velho, com quase 14 quilômetros. Dá para alugar bicicleta e dar a volta inteira pedalando em cima dela. Depois, o Pagode do Ganso Selvagem.", 900, None),
 ("Xi'an", "Guerreiros de Terracota",
  "Um exército de 8.000 soldados de barro em tamanho real, enterrado há 2.200 anos para proteger um imperador depois da morte. Cada rosto é diferente do outro. Ficou escondido até 1974, quando agricultores cavaram um poço e esbarraram nele sem querer. Deixamos para segunda de propósito, porque no fim de semana o lugar fica lotado de visitantes chineses. Vamos com guia particular: sem alguém contando a história, viram só estátuas.", 2200, "destaque"),
 ("Chengdu", "Trem-bala para Chengdu",
  "Mais três horas e meia de trem-bala. Chengdu é a cidade da comida apimentada e das casas de chá, onde as pessoas passam a tarde inteira jogando e conversando.", 600, "trem"),
 ("Chengdu", "Pandas gigantes",
  "A base de pesquisa de pandas. O truque é chegar na hora em que abre: é quando eles estão comendo bambu e se mexendo. Depois das dez da manhã, dormem o dia todo. Tem uma parte só de filhotes.", 800, "destaque"),
 ("Chengdu", "Buda Gigante de Leshan",
  "Um Buda de 71 metros esculpido dentro de uma montanha, terminado no ano 803. É tão grande que uma pessoa sentada no dedão do pé dele parece um grão de arroz. Dá para descer por uma escada cavada na pedra até a base.", 1400, None),
 ("Xangai", "Voo para Xangai e o Bund",
  "Três horas de avião. À noite, o Bund: de um lado do rio, prédios de cem anos; do outro, arranha-céus iluminados. As duas Chinas na mesma foto.", 600, "voo"),
 ("Xangai", "Shanghai Tower",
  "O segundo prédio mais alto do mundo, 632 metros. O elevador sobe a 20 metros por segundo e chega ao 118º andar em menos de um minuto — é o elevador mais rápido que existe.", 1100, "destaque"),
 ("Xangai", "Jardim Yu e cidade velha",
  "Um jardim chinês clássico de 1559, com lagos, pontes em ziguezague — feitas assim de propósito, porque diziam que espírito ruim só anda em linha reta — e muros terminando em cabeça de dragão.", 800, None),
 ("Xangai", "Suzhou",
  "Meia hora de trem-bala. Suzhou é cheia de canais e de jardins tão bonitos que são Patrimônio da Humanidade. Este dia fica para decidir na véspera: se todo mundo estiver cansado, vira dia de descanso em Xangai.", 1400, "opcional"),
 ("Xangai", "Concessão Francesa e despedida",
  "Um bairro que parece Europa no meio da China: prédios franceses, árvores enormes e cafés. Dia de propósito leve — véspera de um voo de 30 horas não é hora de maratona. Comprar o que faltou e jantar de despedida.", 1000, None),
 ("Xangai", "Volta para casa",
  "Voo de Xangai para Guarulhos. Dessa vez o relógio anda para trás.", 300, "voo"),
]

EXTRAS = [("Primeira classe, trem-bala Pequim → Xi'an", 2490),
          ("Primeira classe, trem-bala Xi'an → Chengdu", 1260),
          ("Voo Chengdu → Xangai", 3300)]

SUBTITULO = {"Pequim": "A China dos imperadores, e a Muralha",
             "Xi'an": "A capital mais antiga, e o exército de barro",
             "Chengdu": "Os pandas, e a comida apimentada",
             "Xangai": "A China de hoje, de vidro e altura"}

CAPA_LINHA = ("Pequim, Xi'an, Chengdu e Xangai. A Muralha, um exército de barro enterrado "
              "há 2.200 anos, pandas de verdade e o elevador mais rápido do mundo.")

ANTES_INTRO = ("Três coisas precisam ser resolvidas <strong>aqui no Brasil</strong>. Todas "
               "são difíceis ou impossíveis de resolver depois que o avião pousa.")

ANTES = [
 ("O eSIM da Maya", "{preco} · {linhas} celulares",
  ["Na China, o Google, o WhatsApp, o Instagram e o <strong>Google Maps</strong> são bloqueados. "
   "Um chip chinês comum não resolve, porque passa pelo mesmo bloqueio.",
   "O eSIM é um chip digital instalado pelo aplicativo, e a internet dele sai por fora da China. "
   "Com ele o celular funciona como aqui: mapa para achar o caminho, tradutor apontando a câmera "
   "para o cardápio, e mensagem para a família.",
   "Instalar e <strong>testar ainda em casa</strong>. Instalar já na China é bem mais complicado, "
   "porque o próprio site pode estar bloqueado."]),
 ("Alipay e WeChat Pay", "grátis · instalar os dois",
  ["A China quase não usa dinheiro nem cartão de plástico: paga-se por QR code no celular, até "
   "em barraca de rua. Cartão físico só passa em hotel bom e restaurante turístico.",
   "Os dois aplicativos aceitam cartão internacional desde 2026, sem precisar de conta em banco "
   "chinês. O Alipay é mais fácil de configurar; o WeChat Pay é aceito em mais lugares. "
   "Por isso, os dois.",
   "O cadastro pede foto do passaporte e reconhecimento facial, e leva uns dez minutos. "
   "Limite de ¥5.000 por compra — hotel pago de uma vez passa disso, aí é cartão físico."]),
 ("Escolher os assentos do avião", "grátis · na hora da compra",
  ["São 23 horas de voo até Pequim. Onde a família senta muda bastante como se chega.",
   "A <strong>Resolução ANAC 807/2026</strong> garante que menor de 16 anos sente ao lado do "
   "responsável, com o assento alocado já na compra e <strong>sem taxa extra</strong>. Não é "
   "favor da companhia, é direito — só não vale para assentos de espaço extra, que continuam pagos.",
   "Num avião de corredor duplo, peçam um <strong>trio inteiro de uma das laterais</strong> "
   "(poltronas A-B-C ou H-J-K). A família fica sozinha no bloco, com uma janela e um corredor, "
   "e ninguém passa por cima de estranho a noite toda. O bloco do meio tem gente dos dois lados.",
   "Janela para quem vai dormir encostado — dá para apoiar a cabeça e ninguém esbarra. "
   "Evitar a última fileira (não reclina e fica colada no banheiro) e a fileira em frente ao "
   "banheiro ou à cozinha, que tem luz, barulho e fila a noite inteira. "
   "Quem enjoa deve sentar <strong>em cima da asa</strong>, onde a turbulência é menos sentida."]),
 ("Conferir o nome do cartão", "grátis · faça hoje",
  ["A recusa mais comum no cadastro é o nome do cartão não bater com o do passaporte. "
   "Nome brasileiro longo costuma vir abreviado no plástico.",
   "Confira agora, com um ano de antecedência: se precisar de segunda via com o nome completo, "
   "dá tempo de sobra. Descobrir isso no aeroporto de Pequim é outra história.",
   "E <strong>avise o banco</strong> que haverá compras na China, senão o cartão é bloqueado "
   "por suspeita de fraude logo na primeira."]),
]

GOLPES_INTRO = ("A China é um país seguro para turista, e nada disso é motivo para medo. "
                "Mas existem dois golpes clássicos, e os dois usam exatamente a mesma isca — "
                "vale todo mundo saber, principalmente quem for abordado.")

GOLPES = [
 ("O chá que custa uma fortuna",
  "Um casal de jovens simpáticos, bem vestidos, com inglês muito bom, puxa conversa num ponto "
  "turístico. Dizem que querem praticar o idioma, perguntam de onde você é, quase sempre pedem "
  "uma foto. Depois convidam para tomar um chá ali perto. A conta chega em torno de US$ 100 "
  "por xícara, e discutir não adianta."),
 ("A exposição do amigo artista",
  "Mesma abordagem, outro convite: uma exposição de arte de um estudante, logo ali. Lá dentro, "
  "a pressão para comprar um quadro por um preço absurdo."),
]

GOLPE_REGRA = ("A regra que resolve os dois: <strong>convite para entrar num lugar fechado nunca "
               "vem de quem só quer praticar idioma.</strong> Conversar na rua, tirar foto, "
               "indicar caminho — tudo bem. Aceitar ir junto para um lugar, não.")

GOLPES_EXTRA = ("Mais dois, menores: ônibus não oficiais que prometem levar à Muralha e desviam "
                "para lojas, e táxi oferecido por alguém dentro do aeroporto. Nos dois casos, "
                "a solução é a mesma — usar só a fila oficial ou o aplicativo.")

PRATICOS = [
 "Levar o endereço do hotel <strong>impresso em chinês</strong>. Taxista não lê nosso alfabeto.",
 "Andar com o passaporte todo dia: ele é exigido para comprar bilhete de trem e para passar na revista do metrô.",
 "Levar algum yuan em espécie como reserva — não como meio principal de pagamento.",
]

EMERGENCIA = [("Plantão do Itamaraty, 24h", "+55 61 98260-0610"),
              ("Embaixada em Pequim", "+86 10 6532 2881"),
              ("Plantão de emergência, Pequim", "+86 138 0121 0722"),
              ("Consulado em Xangai", "+86 131 6623 1312")]

CONTAS_INTRO = ("Cada valor é para as <strong>três pessoas juntas</strong>, já convertido "
                "para reais com a cotação oficial do Banco Central e com o IOF incluído.")

AVISO_FALTA = ("As passagens de avião e as noites de hotel não entram na conta acima "
               "porque, com a viagem ainda longe, esses preços não existem: as companhias "
               "só abrem a venda cerca de onze meses antes. Com a viagem inteira, a "
               "estimativa fica entre R$ 48 mil e R$ 57 mil.")

AVISO_VISTO = ("Brasileiro entra na China sem visto, mas essa regra vale até 31 de dezembro "
               "de 2026. Ela já foi prorrogada duas vezes e provavelmente será de novo. Em "
               "novembro de 2026 conferimos: se não for prorrogada, ainda dá tempo de sobra "
               "para tirar o visto.")

RODAPE = ("Cotação CNY/BRL R$ {taxa} — Banco Central, boletim de fechamento.<br>"
          "IOF de {iof} — Decreto 6.306/2007, artigo 15-B.<br>"
          "Preços de passeios são estimativa feita em 2026, a conferir mais perto da viagem.")
