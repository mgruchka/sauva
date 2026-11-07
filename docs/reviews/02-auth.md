# Revisão 02 — autenticação demo

Implementação disponível; integração PostgreSQL pendente. Adicionados modelos `User` e `AuthSession`, migração Alembic, dependência PostgreSQL, Argon2id, seed idempotente e rotas `/auth/login`, `/auth/me` e `/auth/logout`. Login e logout exigem `Origin` exatamente igual a `APP_ORIGIN`. Sessões usam token aleatório no cookie HttpOnly e apenas seu SHA-256 no banco; logout revoga a sessão. `/health` permanece independente do banco.

Arquivos: `app/main.py`, `app/db.py`, `app/models.py`, `app/security.py`, `app/auth.py`, `app/seed.py`, `migrations/env.py`, `migrations/versions/0001_demo_auth.py`, `alembic.ini`, `requirements.txt`, `.env.example`, `README.md`, `docs/STATUS.md` e este relatório.

Verificação: dependências instaladas na `.venv`; compilação e importação OK; Argon2id e `/health` verificados localmente. `python -m pytest tests/test_auth.py tests/test_health.py -q`: um teste health aprovado, cinco erros de setup auth porque falta `TEST_DATABASE_URL` para banco PostgreSQL separado terminado em `_test`. `git diff --check` sem erros. Os testes auth permanecem não verificados. Migração e seed não executados por falta de banco configurado. Nenhuma chamada Google.

Próximo passo: configurar banco de testes e executar novamente o conjunto prescrito antes de aprovar a integração. Não iniciar 03.
