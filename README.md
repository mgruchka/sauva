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
Use Texto para JPEG de documento fotografado. Exame de imagem preserva radiografias e outros originais em FHIR/PDF, sem interpretação diagnóstica e sem Google.

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
Suíte completa: 19 testes, incluindo apenas três novos para o fechamento. É possível passar caminhos ao runner para repetir somente os afetados.
A fidelidade clínica e conformidade completa BR Core não são comprovadas pelo validador estrutural. Pastas planas, anexos de imagem médica, PDF local e compartilhamento estão implementados; o aceite PostgreSQL final segue a tarefa 06.

## Demonstração completa — fechamento

Siga `docs/tasks/06-prototype-finish.md` para sincronizar, aplicar migração,
importar os quatro exemplos e iniciar. A importação usa FHIR salvo e não chama Google:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m app.seed
.\.venv\Scripts\python.exe scripts/import_demo_documents.py
.\.venv\Scripts\python.exe scripts/run_tests.py
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

A interface inclui pastas planas, nomes, originais privados e JSON/PDF. Exames de
imagem preservam o original em FHIR sem interpretação diagnóstica. O PDF é gerado
localmente dos dados armazenados, sem custo de IA adicional, com template provisório.
Compartilhamento exige outra conta cadastrada: link/senha valem 24h, resgate único
abre acesso de 10min para visualizar e baixar somente o documento escolhido.
Use demo1 como proprietário e demo2 como destinatário. Dados sintéticos apenas.
