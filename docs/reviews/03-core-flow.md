# Revisão 03 — caminho principal
Implementação concluída: `app/documents.py`, `app/extraction.py`, `app/conversion.py`, `app/fhir.py`, modelo/migração de documentos, `web/` e ajustes em `app/main.py`, dependências, `.env.example` e README. Upload Texto PDF/JPEG com limites, arquivo privado por usuário, processamento serial, OCR de páginas sem texto, conversão Gemini em duas etapas, validação estrutural, rotas de consulta/renomeação/download JSON e tela mínima em pt-BR.

Migração `0002_documents`: saída 0. `scripts/run_tests.py`: **11 passed in 6.01s**. `node --check web/app.js`, `pip check` e `git diff --check`: OK. Home, JS e logo retornaram HTTP 200 via TestClient. Caminhada manual no navegador não realizada.

Testes usaram OCR/conversor simulados; nenhuma chamada Google real. Os prompts são rascunhos e exigem revisão de Marcos antes de ativar `FHIR_PROMPT_APPROVED` e `ENABLE_REAL_GOOGLE`. Credenciais e modelo Google serão necessários apenas para smoke sintético posterior. FHIR recebe validação estrutural local, sem certificação BR Core ou clínica. A fila é local e pendências interrompidas por reinício não são repetidas automaticamente.

Pronto para revisão da tarefa 03. Não iniciar etapas seguintes.
