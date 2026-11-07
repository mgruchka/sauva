# Revisão 02 — autenticação demo

Implementação publicada em `dev/foundation`: modelos User/AuthSession, migração Alembic, conexão PostgreSQL, Argon2id, seed idempotente, endpoints login/me/logout, cookie HttpOnly de oito horas e validação exata de Origin. Arquivos de código e documentação da tarefa 02 permanecem no commit anterior; esta atualização registra a verificação local.

PostgreSQL 18 local em execução. `.\.venv\Scripts\python.exe -m alembic upgrade head`: saída 0. `.\.venv\Scripts\python.exe scripts/run_tests.py`: saída 0, **6 passed, 1 warning in 7.21s**; cinco testes auth e um health aprovados. O aviso é de depreciação do TestClient.

Após configuração local das senhas DEMO_*, `.\.venv\Scripts\python.exe -m app.seed` concluiu duas vezes com saída 0 e mensagem `Contas de demonstração prontas.` A segunda execução confirmou o caminho idempotente; nenhuma senha ou hash foi exibido. Migração e testes não foram repetidos nesta rodada porque o código não mudou.

**Tarefa 02 pronta para revisão.** Não iniciar 03.
