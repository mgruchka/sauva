# 01 — fundação executável sem APIs externas

Dependência: tarefa 00 sem bloqueios. Execute somente esta etapa e pare.

## Ler
AGENTS.md, docs/PROJECT.md, docs/STATUS.md, tests/test_health.py. Não ler DOCX/PDF, FHIR examples, SVG ou guidelines.

## Entrega
- app/__init__.py e app/main.py com create_app() -> FastAPI e app = create_app().
- GET /health público retorna HTTP 200 e {"status":"ok"}. Endpoint indica apenas processo vivo, não prontidão do banco/Google.
- Inicialização e /health não exigem banco, chave Gemini, Vision, rede externa ou credenciais.
- Dependências mínimas em requirements.txt e requirements-dev.txt: FastAPI/Uvicorn e pytest/httpx para desenvolvimento. Use releases estáveis compatíveis com o intérprete identificado. Não adicionar ORM/Google SDK/frontend nesta tarefa.
- .gitignore para .venv/, .env e variantes locais (preservar .env.example), __pycache__/, .pytest_cache/, uploads/, arquivos gerados e credenciais locais. Não ignorar exemplos JSON versionados em agent-files/.
- .env.example com placeholders vazios para GEMINI_API_KEY, GEMINI_MODEL, GOOGLE_CLOUD_PROJECT, DATABASE_URL. Nenhum valor real, serviço ou modelo assumido.
- README.md curto em pt-BR: ambiente virtual, instalação, comando para rodar e testar, /docs e /health; avise que apenas fundação existe.
- scripts de PowerShell opcionais só se necessários. Nenhum Docker/WSL obrigatório.

## Verificar
Use .venv no projeto e seu Python explícito. Não altere a instalação global.
Instale requirements-dev.txt; este deve incluir requirements.txt.
Execute com o Python do ambiente: -m pytest tests/test_health.py -q.
Verifique import app.main e a documentação em /docs por TestClient ou inspeção local. Não adicionar testes apenas para espelhar implementação.
Não use --reload em processo persistente para a verificação; encerre qualquer servidor iniciado.

## Limites
Não implementar auth, banco, uploads, UI, Gemini, OCR, PDF ou compartilhamento.
Não editar tests/test_health.py. Se o contrato for inviável explique antes de alterá-lo.
Não fazer chamadas Google e não imprimir segredos.
Sem push/commit automático. Atualize docs/STATUS.md com resultado real e pendências; mostre diff resumido.
Ao terminar pare para revisão do orquestrador, sem iniciar 02.
