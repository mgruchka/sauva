# Revisão 02 — autenticação demo

**Implementação disponível; integração PostgreSQL pendente.**

Entrega: modelos User/AuthSession, Alembic, PostgreSQL/psycopg, Argon2id, seed idempotente e login/me/logout. Cookie HttpOnly de oito horas, apenas SHA-256 do token persistido e origem exata obrigatória nos POSTs.

Verificação anterior: importação, compilação, Argon2id e health OK; pytest teve um health aprovado e cinco erros de setup auth por TEST_DATABASE_URL ausente. Nenhuma chamada Google.

O orquestrador ajustou o carregamento de `.env` na migração e adicionou `scripts/run_tests.py` e `docs/POSTGRES_LOCAL.md`. Testes originais preservados.

Verificação local após `git pull --ff-only origin dev/foundation`: PostgreSQL 18 encontrado fora do PATH, serviço `postgresql-x64-18` em execução. A conexão sem senha (`psql -w -h 127.0.0.1 -U postgres -d postgres -tAc 'SELECT 1'`) retornou `fe_sendauth: no password supplied`. `.env` não existia; foi criado a partir de `.env.example` e confirmado como ignorado pelo Git. Nenhuma credencial real foi lida ou publicada. Migração, seed e `scripts/run_tests.py` não executados porque ainda faltam acesso local e configuração dos bancos; cinco testes auth permanecem não aprovados.

Ação do Marcos: usar SQL Shell com a senha administrativa local, conferir `\du` e `\l`, criar apenas role/bancos ausentes e definir senha da role conforme docs/POSTGRES_LOCAL.md. Preencher `.env` com as duas URLs e senhas demo sem enviá-las pelo chat. Depois executar migração, seed e testes. **Integração PostgreSQL pendente; não iniciar 03.**
