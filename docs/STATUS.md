# Estado
- Branch: dev/foundation.
- Implementados: autenticação demo, Texto PDF/JPEG -> Gemini/FHIR, OCR multimodal, imagem médica como anexo sem diagnóstico, original privado, JSON/PDF local, pastas planas, compartilhamento de resgate único e interface.
- Exemplos textuais normalizados disponíveis; importação idempotente coloca os quatro exemplos em demo1 sem novas chamadas Google nem alteração do ledger.
- Verificado pelo orquestrador: sete testes + sete subtestes, quatro PDFs, compilação Python/JS, startup/assets/health, compilação SQL das três migrações.
- Pendente local: aplicar 0003, seed/importação, executar testes PostgreSQL existentes e dois novos de integração, caminhada rápida na interface.
- Próxima ação: docs/tasks/06-prototype-finish.md. Não repetir chamadas Gemini dos textos; preservar ledger e segredos.
