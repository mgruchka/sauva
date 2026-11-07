# Estado

- Tarefa 03 implementada: upload Texto PDF/JPEG, extração local/OCR por página, processamento serial, conversão Gemini em duas etapas, validação estrutural FHIR, listagem/status/renomeação/download JSON e interface mínima em pt-BR.
- Migração `0002_documents` executada localmente com saída 0. Dependências mínimas instaladas e versões fixadas.
- `scripts/run_tests.py`: **11 passed in 6.01s** (5 documentos, 5 auth, 1 health). `node --check web/app.js`, `pip check`, `git diff --check`: OK. Home, JS e logo: HTTP 200 via TestClient.
- Interface: assets servidos; caminhada manual no navegador não realizada. Nenhuma chamada Google real executada. Adaptadores simulados usados nos testes.
- Pendências: revisão dos rascunhos `prompts/01-extract.md` e `prompts/02-map-fhir.md` por Marcos antes de ativar as flags reais; credenciais/modelo Google para smoke futuro. A validação é estrutural, sem conformidade BR Core ou correção clínica certificadas.
- Próxima ação: revisão do orquestrador. Não iniciar 04 nem funcionalidades adiadas.
