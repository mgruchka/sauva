# Estado
- Autenticação e fluxo de documentos já implementados. Worker reportou onze testes aprovados antes da revisão/refatoração.
- Refatoração atual aprovada por Marcos: Gemini-only, sem Cloud Vision. PDF textual extrai localmente; JPEG/PDF digitalizado/misto recebe transcrição/fatos multimodais e mapeamento em até duas chamadas Gemini por documento.
- Adaptadores mockados atualizados: cinco testes executados pelo orquestrador, aprovados, incluindo PDF textual, PDF digitalizado de duas páginas e JPEG. Nenhuma API real ou banco foi usado pelo orquestrador.
- requirements.txt sem google-cloud-vision. Nenhuma dependência adicionada.
- scripts/validate_demo_files.py atualizado: ledger novo generated/demo-gemini/, erros sanitizados, candidato preservado e retry somente explícito. Vision antigo não será repetido.
- Próxima ação local: seguir docs/GEMINI_ONLY.md. Executar onze testes relevantes e os três exemplos de texto com chave local; publicar resultados para revisão. Não repetir auth nem reimplementar a aplicação.
- Nenhum teste Gemini real foi executado neste ambiente, que não tem acesso ao .env do Marcos.
- Radiografia example_imaging.jpeg continua com pipeline pendente; não contar como aprovada.
