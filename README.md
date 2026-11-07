# SAÚVA

Protótipo brasileiro com FastAPI, PostgreSQL e interface HTML/JS. Upload Texto PDF/JPEG -> transcrição/extração -> FHIR JSON.

## Gemini-only
A integração de IA usa somente Gemini Developer API. Não requer Cloud Vision, ADC, chave de serviço ou faturamento Vision.
- PDF totalmente textual: extração local, depois duas etapas Gemini.
- JPEG ou PDF digitalizado/misto: leitura do arquivo e extração de fatos em uma chamada Gemini; mapeamento FHIR em outra.
- No máximo duas chamadas por documento, sem retentativas automáticas.
Configurar GEMINI_API_KEY e GEMINI_MODEL no .env local. Nunca commitar chaves.
Para interface web, habilitar ENABLE_REAL_GOOGLE=true e FHIR_PROMPT_APPROVED=true após autorização dos prompts (já dada para exemplos fictícios) e reiniciar o servidor.

[Executar os exemplos e diagnosticar erros](docs/GEMINI_ONLY.md). Resultados ficam em generated/demo-gemini/. O erro Vision anterior foi preservado em outro ledger, sem ser repetido.
Radiografias e outras imagens médicas ainda não são processadas; JPEG aqui significa documento de texto fotografado.

## Ambiente local
Python 3.13 e .venv existente. Em PowerShell:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```
Não recriar ambiente já funcional. Nenhuma nova dependência foi adicionada na refatoração Gemini-only.

## PostgreSQL e contas
Seguir [PostgreSQL local](docs/POSTGRES_LOCAL.md); bancos separados sauva e sauva_test.
Contas: demo1@sauva.example e demo2@sauva.example. As senhas DEMO_OWNER_PASSWORD/DEMO_RECIPIENT_PASSWORD ficam locais; seed não redefine contas existentes.
```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m app.seed
```
Se migração/seed já concluíram, não repetir sem necessidade.

## Executar
```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
```
Abrir http://127.0.0.1:8000; /docs documenta API, /health indica somente processo vivo.
Upload Texto: até 10 MB e PDF até 10 páginas. Originais privados em uploads/, fora do Git. Fila serial em memória; reinício não repete chamadas automaticamente.

## Testar
```powershell
.\.venv\Scripts\python.exe scripts/run_tests.py
```
Suíte completa de 16 testes; a rodada de refatoração usa somente os onze pertinentes indicados em docs/GEMINI_ONLY.md.
A fidelidade clínica e conformidade completa BR Core não são comprovadas pelo validador estrutural. Pastas, imagens médicas, PDF de saída e compartilhamento ainda pendentes.
