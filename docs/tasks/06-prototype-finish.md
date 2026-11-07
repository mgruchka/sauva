# 06 — Fechar e iniciar o protótipo agora

Marcos autorizou concluir o protótipo dentro de uma hora, simplificar escopo e reduzir testes novos. Esta tarefa consolidada substitui pausas entre etapas antigas. Código já publicado pelo orquestrador; execute integração e corrija bloqueios concretos sem pedir nova autorização.

## Escopo entregue
Imagem PDF/JPEG anexada em DocumentReference sem diagnóstico/Google; PDF determinístico local do FHIR/transcrição; pastas planas; link/senha para uma conta destinatária com validade 24h e resgate único que abre sessão de 10min para visualizar/baixar um documento. Cinco senhas incorretas bloqueiam o link. Interface em pt-BR com CSS local. Original disponível mesmo quando conversão falha. Importação idempotente dos quatro exemplos em demo1, dos resultados salvos, sem Google nem mudança no ledger.

## Executar no PowerShell, raiz do projeto
1. Preservar mudanças locais conhecidas; sincronizar dev/foundation sem descarte/force-push. Não incluir segredos nem generated/.
2. `.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt`
3. `.\.venv\Scripts\python.exe -m alembic upgrade head`
4. `.\.venv\Scripts\python.exe -m app.seed` (idempotente; senhas já preenchidas).
5. `.\.venv\Scripts\python.exe scripts/import_demo_documents.py`
6. `.\.venv\Scripts\python.exe scripts/run_tests.py` — testes existentes mais APENAS três novos, sem Google. Carrega .env; não remover testes existentes para reduzir contagem.
7. `node --check web/app.js` e `git diff --check`.
8. `.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000`; conferir APP_ORIGIN correspondente em .env sem expor valores. Abrir http://127.0.0.1:8000.

## Caminhada curta
- Login demo1: quatro exemplos prontos; abrir original, JSON e PDF. Criar pasta, mover/filtrar um documento.
- Compartilhar um pronto com demo2; copiar link/senha. Sair, abrir link e entrar como demo2, ou usar janela privada.
- Resgatar; abrir original/JSON/PDF dentro de 10min. Novo resgate deve falhar como usado; sessão já aberta continua válida até expirar.
- Upload example_imaging.jpeg como Exame de imagem: deve ficar pronto sem Google.
- Não repetir conversão Gemini dos textos; resultados salvos bastam. Runner real agora inclui imagem sem API, respeita ledger e continua após falha individual; `scripts/validate_demo_files.py --file example_imaging.jpeg` é opcional para atualizar esse registro no ledger.

Se houver erro, corrigir neste escopo e executar somente testes afetados. Falha de documento não deve parar servidor ou arquivos independentes. PostgreSQL inacessível é bloqueio real; não substituir por SQLite. Os testes de integração devem rodar aqui: o orquestrador não acessa seu banco/credenciais.

Atualizar docs/STATUS.md e docs/reviews/06-prototype.md com resultados reais e pendências. Revisar allowlist/staged diff; commit/push normal dev/foundation autorizado. Não fazer deploy/merge. Encerrar com SHA e estado em até 150 palavras. Não parar para novas etapas de planejamento.
