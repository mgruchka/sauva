# 02 — contas de demonstração e autenticação (proposta para confirmação)

Estado: NÃO EXECUTAR IMPLEMENTAÇÃO AINDA. Marcos confirmou contas pré-criadas. Confirmar o desenho abaixo antes de programar. O orquestrador fornecerá os testes executáveis após essa confirmação; os casos abaixo já definem o aceite.

## Contexto mínimo
Leia AGENTS.md, docs/PROJECT.md, docs/STATUS.md, app/main.py, requirements*.txt e esta tarefa. Não ler estudo, exemplos FHIR ou identidade visual. Não alterar a fundação aprovada sem necessidade demonstrada.
Não iniciar uploads, OCR, frontend, FHIR ou compartilhamento.

## Confirmado
- Contas pré-criadas de demonstração. Sem autocadastro nesta entrega.
- Backend FastAPI e banco PostgreSQL, conforme escopo original.
- A saúde pública GET /health deve continuar funcionando sem Google ou banco.

## Desenho proposto (pendente de confirmação de Marcos)
- Duas contas independentes: demo1@sauva.example e demo2@sauva.example. Ambas com mesmas permissões; representam proprietário e destinatário apenas durante a demonstração. Não criar papel administrador sem necessidade.
- Login com email/senha; sem verificação de email, recuperação de senha ou rota de cadastro.
- Sessões opacas persistidas no PostgreSQL, identificadas por cookie HttpOnly, SameSite=Lax, Path=/, duração de 8 horas; logout revoga a sessão no servidor.
- Desenvolvimento em http://127.0.0.1:8000 com Secure=False somente no ambiente local; Secure=True quando houver HTTPS. Nunca guardar token em localStorage.
- Frontend futuro servido pela mesma origem do FastAPI. Verificar Origin nas requisições mutáveis de navegador; proibir origem externa e não habilitar CORS irrestrito. Política para clientes sem Origin deve ser explícita nos testes antes de implementar.
- SQLAlchemy síncrono + psycopg e migrações Alembic. Senhas com Argon2id. Detalhes de dependências e versões serão limitados às bibliotecas necessárias, sem extras assíncronos.

## Contrato proposto
- POST /auth/login recebe JSON {email, password}; sucesso 200 com {id, email} e Set-Cookie sauva_session. Falha 401 com mensagem genérica em pt-BR para usuário inexistente e senha incorreta.
- GET /auth/me retorna {id, email}, ou 401 quando não autenticado/expirado.
- POST /auth/logout revoga token no servidor e remove cookie; resposta 204, inclusive sem sessão.
- Não expor hashes ou tokens no JSON, logs ou relatórios do agente.
- Não implementar texto de política/consentimento ou tela de login nesta tarefa; confirmar com Marcos na etapa da interface.

## Persistência
- users: UUID, email normalizado e único, password_hash, created_at.
- sessions: hash único do token aleatório criptograficamente seguro, user_id, created_at, expires_at. Nunca armazenar token bruto no banco.
- Script explícito de seed idempotente, sem execução automática no startup.
- DEMO_OWNER_PASSWORD e DEMO_RECIPIENT_PASSWORD entram localmente por configuração; não incluir valores reais em .env.example ou no Git. Reexecutar seed preserva UUIDs e não redefine senhas silenciosamente.
- Banco de testes PostgreSQL separado, configurado por TEST_DATABASE_URL. Nenhuma limpeza automática do banco de desenvolvimento; não substituir por SQLite por conveniência.
- Ausência de PostgreSQL/credenciais bloqueia somente testes de banco e auth. Não afirmar que testes passaram se não foram executados.

## Aceite definido pelo orquestrador (máximo 5 testes)
1. Seed executado duas vezes preserva exatamente duas contas e seus UUIDs; senhas verificáveis por hash, sem texto puro.
2. Login correto emite cookie com atributos previstos e /auth/me identifica exatamente a conta conectada; nenhum segredo aparece na resposta.
3. Senha incorreta e email inexistente retornam o mesmo erro genérico 401; sem criar sessão.
4. Sessão ausente/expirada rejeitada; logout invalida token também quando o cookie antigo é reapresentado.
5. Origem externa não pode executar login/logout nem criar/revogar sessão; um pedido legítimo da origem local funciona conforme política confirmada.
Executar também tests/test_health.py após integração. Testes de arquivos/isolamento por proprietário pertencem à etapa 03.

## Relatório e parada
Relatar até 200 palavras com arquivos alterados, testes executados/resultados e bloqueios. Mostrar diff relevante. Não repetir preflight inteiro, não chamar Google, não fazer push/commit, não iniciar 03.
