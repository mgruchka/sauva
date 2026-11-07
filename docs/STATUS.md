# Estado
- Autenticação 02 aceita para o protótipo: revisão estática realizada; seis testes aprovados e seed idempotente reportados pelo agente local no commit 35b441a.
- Prioridade aprovada por Marcos: caminho Texto -> extração/OCR -> Gemini -> FHIR JSON antes das funcionalidades secundárias.
- Tarefa atual: docs/tasks/03-core-flow.md, liberada para implementação completa com adaptadores Google simulados nos testes.
- Testes fornecidos: tests/test_documents.py (5) + auth (5) + health (1). Novos testes ainda não executados.
- SDKs reais devem ser implementados; chamadas reais aguardam revisão dos rascunhos prompts/01-extract.md e prompts/02-map-fhir.md conforme instrução original. Não bloquear a escrita do código por isso.
- Próxima ação: agente local implementa, testa, publica relatório/código em dev/foundation e para para revisão. Não voltar ao preflight/auth nem iniciar itens adiados.
