# Gemini-only — revisão e resultados
Refatoração pelo orquestrador: sem Vision/ADC; até duas chamadas Gemini por documento, inclusive PDF misto ou JPEG.
Verificação do orquestrador: cinco regressões com SDK simulado aprovadas, incluindo envio PDF/JPEG e extração local do PDF textual. Não executou API real, SDK instalado ou PostgreSQL neste ambiente.
Aguardando agente local executar os onze testes pertinentes e os três exemplos com a chave local. Atualizar aqui resultados reais, erros sanitizados e saídas publicadas; não incluir segredos. A radiografia continua pendente.
