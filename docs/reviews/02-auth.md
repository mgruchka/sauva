# Revisão 02 — autenticação demo

Implementação publicada em `dev/foundation`: modelos User/AuthSession, migração Alembic, conexão PostgreSQL, Argon2id, seed idempotente, endpoints login/me/logout, cookie HttpOnly de oito horas e validação exata de Origin. Arquivos de código e documentação da tarefa 02 permanecem no commit anterior; esta atualização registra a verificação local.

PostgreSQL 18 local em execução. `.\.venv\Scripts\python.exe -m alembic upgrade head`: saída 0. `.\.venv\Scripts\python.exe scripts/run_tests.py`: saída 0, **6 passed, 1 warning in 7.21s**; cinco testes auth e um health aprovados. O aviso é de depreciação do TestClient.

`.\.venv\Scripts\python.exe -m app.seed`: saída 1, `Configure DATABASE_URL e as duas senhas DEMO_* antes do seed.` Conferência de presença sem revelar valores: `DATABASE_URL` e `TEST_DATABASE_URL` presentes; ambas as senhas DEMO_* ausentes ou vazias. Nenhuma conta demo operacional criada pelo seed nesta rodada.

Próxima ação do Marcos: preencher as duas senhas DEMO_* localmente em `.env` e repetir o seed. Não enviar credenciais pelo chat. **Integração técnica aprovada; seed operacional pendente.** Não iniciar 03.
