# 02 — autenticação com contas de demonstração

Estado: comportamento aprovado por Marcos. Tarefa liberada com testes do orquestrador.
Executar somente 02; publicar código e relatório em dev/foundation e parar para revisão.

## Primeiro: sincronizar sem perder a fundação local
A fundação 01 foi aprovada pelo orquestrador pelo código compartilhado e teste local aprovado, mas ainda não está no GitHub.
Marcos autorizou agora commits e push de arquivos da tarefa para dev/foundation. Isso substitui as antigas proibições de commit/push para o handoff destas tarefas.
1. Inspecionar status e diff, incluindo não rastreados. Confirmar app/__init__.py com dois underscores.
2. Fazer checkpoint da fundação aprovada com allowlist: app/__init__.py, app/main.py, requirements.txt, requirements-dev.txt, .gitignore, .env.example, README.md, docs/STATUS.md e teste health corrigido se houver diferença legítima.
3. Não adicionar .env, credenciais ou arquivos desconhecidos; revisar git diff --cached --stat e diff dos arquivos de texto antes do commit.
4. Fazer fetch e integrar origin/dev/foundation preservando o checkpoint. Rebase local é permitido; não usar reset --hard, clean, force-push ou descartar mudanças. Se houver conflito ambíguo, parar e informar.
5. Ler os arquivos desta tarefa na versão atualizada antes de implementar. Não reconstruir a fundação do zero.
Se este arquivo não estiver local ainda, as mesmas instruções estão no prompt de handoff do Marcos.

## Ler apenas
AGENTS.md, docs/PROJECT.md, docs/STATUS.md, esta tarefa, tests/test_auth.py, app/main.py e dependências atuais; abrir código diretamente relacionado quando necessário.
Não ler agent-files/, estudo PDF ou exemplos FHIR nesta etapa.

## Comportamento aprovado
- Duas contas: demo1@sauva.example e demo2@sauva.example, mesmas permissões. Login com email/senha.
- Sem cadastro, recuperação, verificação de email ou administrador.
- Cookie sauva_session: HttpOnly, SameSite=Lax, Path=/, Max-Age=28800. Sessão no servidor expira em 8 h e logout a revoga imediatamente.
- Secure=False apenas em desenvolvimento HTTP local; True em HTTPS. Token nunca em localStorage.
- Frontend futuro na mesma origem do backend. Para POST /auth/login e /auth/logout exigir Origin EXATAMENTE igual a APP_ORIGIN. Ausente, null, prefixos e origem externa -> 403 antes de efeitos no banco. Clientes CLI devem enviar Origin explicitamente. Sem CORS irrestrito.
- /health continua público e independente de PostgreSQL/Google, inclusive no startup.

## Contratos executáveis dos testes
- create_app(*, database_url=None, allowed_origin=None, cookie_secure=None), mantendo chamada sem argumentos. Argumentos explícitos sobrescrevem configuração local.
- app.db.get_db: dependência FastAPI compartilhada que fornece Session. Não capturar função equivalente diferente, pois dependency_overrides deve funcionar.
- app.models.User: id UUID, email normalizado/único, password_hash, created_at.
- app.models.AuthSession: user_id, token_hash único, created_at, expires_at com timezone. Token aleatório de secrets, ao menos 32 bytes de entropia; armazenar somente SHA-256 hexadecimal do token.
- app.security.verify_password(password, password_hash) -> bool; usar Argon2id e erro de credencial genérico.
- app.seed.seed_demo_accounts(db, *, owner_password, recipient_password): idempotente, não redefine senhas nem IDs existentes. Aceita Session do chamador; sem criar engine/conexão paralela. Não apagar contas existentes.
- POST /auth/login JSON {email,password}: 200 {id,email} e cookie; credencial inválida -> 401 {"detail":"Email ou senha inválidos."}.
- GET /auth/me: 200 {id,email}, ou 401 para cookie ausente/inválido/expirado/revogado. Não retornar hashes ou token em JSON.
- POST /auth/logout: 204 sem corpo, revoga sessão e remove cookie; idempotente para origem permitida mesmo sem sessão.
- SQLAlchemy síncrono + psycopg; Alembic em migrations/ e alembic.ini. Tipos/modelos sem schema public fixo.
- migrations/env.py deve respeitar config.attributes["connection"] quando fornecida pelos testes; nesse caso não abrir outra conexão. Migrações normais usam DATABASE_URL.
- Nenhuma criação de tabelas, migração ou seed automática no import/startup. Acesso ao banco só quando necessário.
- Ler .env local para operação é permitido, sem exibir seu conteúdo ou valores. Não sobrescrever .env existente; não imprimir URLs/chaves. Google não é necessário aqui.

## Arquivos e execução local
Arquivos esperados: app/db.py, app/models.py, app/security.py, app/auth.py, app/seed.py; atualizar main.py e dependências. Criar módulo de configuração apenas se necessário; evitar camadas extras.
Adicionar às dependências apenas SQLAlchemy, psycopg com instalação Windows adequada, Alembic, Argon2 e carregamento .env se necessário. Reutilizar .venv; fixar versões compatíveis instaladas.
.env.example: placeholders para DATABASE_URL, TEST_DATABASE_URL, APP_ORIGIN (http://127.0.0.1:8000), SESSION_COOKIE_SECURE (false local), DEMO_OWNER_PASSWORD, DEMO_RECIPIENT_PASSWORD; preservar os placeholders Google.
Script explícito python -m app.seed: senhas vêm do ambiente; se ausentes, erro compreensível sem seed parcial. Nunca salvar senhas da demonstração no Git; constantes nos testes são exclusivamente fixtures sintéticas.
README pt-BR: criar/configurar dois bancos locais separados (sauva e sauva_test), migração, seed, teste e login. Não instalar PostgreSQL como serviço nem redefinir senhas sem orientar Marcos; não presumir credenciais.
Se PostgreSQL ou banco de testes não existir, implementar a parte autorizada e informar a configuração que falta. Não substituir por SQLite nem registrar testes como aprovados.

## Verificação prescrita
Não alterar tests/test_auth.py ou tests/test_health.py para fazer implementação passar.
O teste auth cria SOMENTE um schema exclusivo sauva_test_<uuid> no banco terminado em _test, executa migrações e remove esse schema ao final; cada caso usa rollback. Nunca limpar banco inteiro.
Não editar fixtures para apontar ao banco de desenvolvimento. TEST_DATABASE_URL deve existir no ambiente do processo de testes (o teste não lê .env).
Executar:
- Python de .venv: -m pytest tests/test_auth.py tests/test_health.py -q
- git diff --check
São cinco testes auth e uma regressão health. Não executar chamadas Google.
Se houver falha de contrato do próprio teste, preservar e relatar ao orquestrador. Se erro persistir após duas tentativas relevantes, registrar bloqueio.

## Handoff autorizado
Atualizar docs/STATUS.md e docs/reviews/02-auth.md com comandos, versões relevantes, resultados reais (aprovados/falhos/não executados), pendências e lista de arquivos. Relatório até 250 palavras, sem dumps de logs ou segredos.
Revisar e adicionar somente arquivos da tarefa; conferir staged diff; commit(s) descritivos e push normal para origin dev/foundation autorizados.
Se o remoto avançou, fetch e reconciliar sem sobrescrever trabalho; nunca force-push. Bloqueio de autenticação GitHub -> orientar Marcos, não pedir token no chat.
Não fazer merge/deploy, não iniciar 03 e não publicar .env/bancos/uploads. Encerrar com SHA do commit publicado e estado: pronto para revisão ou bloqueado.
