# 03 — caminho principal: upload Texto -> extração/OCR -> Gemini -> JSON

LIBERADA. Marcos aprovou PDF/JPEG, 10 MB/10 páginas, originais locais em uploads/, um documento processado por vez, foco Texto. Implementar toda esta tarefa, publicar em dev/foundation e parar para revisão. Não retornar apenas plano/preflight.
A autenticação 02 está aceita para o protótipo: seis testes aprovados e seed operacional reportados. Não repetir sua implementação.

## Contexto mínimo
Ler AGENTS.md, docs/PROJECT.md, este arquivo, tests/test_documents.py, app/main.py, app/auth.py, app/db.py, app/models.py e dependências. Somente para UI: agent-files/style-guidelines.md e logo. Somente para converter: prompts/ e docs/FHIR_SCOPE.md. Não carregar bundles completos ou estudo no contexto a cada etapa.
Sincronizar remoto preservando trabalho local; commit/push normal da tarefa já autorizado.

## Entrega em um ciclo
1. Migração documents e serviço de arquivos isolado por usuário.
2. Extração PDF textual/misto e OCR JPEG por adaptador Vision.
3. Adaptador Gemini em dois passos e validação local honesta.
4. Rotas listar/status/renomear/baixar JSON.
5. Tela mínima de login + upload + lista com status + download JSON. Não é a versão visual final.
6. Executar os testes prescritos, atualizar relatório e publicar código.
Faltas de credenciais Google bloqueiam SOMENTE o smoke real; implementar e validar todo o resto com os adaptadores injetados. Não esperar revisão entre os itens acima.

## Arquivos / contratos
Reutilizar autenticação; expor current_user/check_origin como dependências reutilizáveis se preciso, preservando testes auth.
create_app mantém argumentos existentes e acrescenta storage_dir=None, ocr=None, converter=None, jobs_inline=False.
ocr: callable(bytes JPEG) -> str. converter: callable(texto completo) -> dict Bundle. Injetados somente por código/testes, nunca por parâmetros HTTP.
Implementar módulos curtos app/documents.py, app/extraction.py, app/conversion.py, app/fhir.py (outros só se necessários).
Document: UUID id, user_id FK, name, original_name, document_type, file_format, storage_path privado, status, stage, error nullable, extracted_text nullable, fhir_payload JSONB nullable, validation_level nullable, created_at/extracted_at com timezone.
Não expor storage_path/extracted_text nem exceções dos provedores em respostas, listagens ou logs.
Novas dependências mínimas: python-multipart, pypdf, pypdfium2, Pillow, google-cloud-vision, google-genai; reportlab em dev para fixtures PDF. Sem Java, Redis, Celery ou containers novos. Fixar versões compatíveis efetivamente instaladas.

## HTTP
- POST /documents multipart file, document_type=Texto, name opcional -> 202 com id/status. Requer sessão e Origin exata como auth.
- GET /documents -> lista JSON dos documentos do usuário, do mais recente ao mais antigo.
- GET /documents/{id} -> metadados/status; 404 para inexistente OU de outro usuário.
- PATCH /documents/{id} JSON {name} -> metadados atualizados; sessão+Origin; não converter novamente.
- GET /documents/{id}/json -> Bundle armazenado, Content-Type application/json e Content-Disposition attachment; 409 se não ready; sessão, 404 para outro proprietário.
- Metadados incluem id,name,status,stage,error,created_at,validation_level.
- status: queued, processing, ready, error. UI traduz para pt-BR e mostra estágio atual.
- Texto apenas nesta etapa; Exame de imagem deve retornar 422 compreensível, sem interpretação/fallback.
- Validar UUIDs e nomes vazios; nome de exibição nunca define caminho de armazenamento.

## Armazenamento e validação de entrada
10 MB = 10_000_000 bytes; ler upload incrementalmente com limite, sem carregar corpos arbitrários.
PDF/JPEG confirmados pelo conteúdo e formato/extensão coerentes, não apenas MIME declarado. PNG/outros ->415. PDF/JPEG corrompido, PDF criptografado ou >10 páginas ->422. >10 MB ->413.
Validar limites e contagem de páginas ANTES de persistir original definitivo, criar Document ou chamar provedor; remover temporários em falha.
Salvar original em uploads/<user_uuid>/<document_uuid>.pdf ou .jpg, fora do Git e sem StaticFiles público. Nenhum caminho derivado do nome enviado; resolver contenção na raiz.
Manter originais para a demonstração; nenhum apagamento/retention job automático nesta etapa.

## Extração
PDF: usar extração local por página (pypdf). Página com texto não vazio após strip usa esse texto. Página sem texto: renderizar localmente JPEG com pypdfium2/Pillow e chamar OCR. Preservar ordem e separadores de página. PDF misto NÃO pode descartar páginas digitalizadas.
JPEG Texto: normalizar bytes JPEG quando necessário e passar ao OCR.
Fechar imagens/PDF/bitmaps; renderizar uma página por vez com resolução limitada para RAM (aprox.150 dpi), sem subprocessos externos.
Vision oficial: ImageAnnotatorClient e text_detection, ADC/GOOGLE_APPLICATION_CREDENTIALS suportados; cliente só quando necessário. Tratar resposta.error, ausência de texto, timeout/credencial inválida como falha do documento com mensagem pt-BR sanitizada. Sem resultado falso bem-sucedido.
Não configurar GCS para este caminho: PDFs são renderizados localmente por página.
Timeout por chamada e sem retentativas automáticas cobradas. OCR no máximo uma chamada por página que precise dele.

## Processamento serial e persistência
Um executor por aplicação com max_workers=1, servidor local uvicorn --workers 1. Nada de iniciar um executor/cliente Google por polling.
POST persiste queued e agenda trabalho; processamento registra/commita estágios e ready/error.
Job de produção abre sua própria Session e a fecha; não reutilizar Session encerrada da requisição.
jobs_inline=True executa sincronamente usando a Session da dependência sobrescrita nos testes; o POST continua retornando 202. Não abrir conexão fora do schema isolado dos testes.
Fakes cobrem tudo sem Google. Produção sem configuração Google deve dar erro claro; NUNCA usar fake como fallback para usuário real.
Listar, consultar status, renomear e baixar não fazem nova inferência.
Fila deste protótipo é em memória: documentar que reinício interrompe pendências; não reexecutar chamadas pagas automaticamente e não apresentar pendentes como concluídos.

## Gemini e FHIR
Criar adaptador real google-genai sem chamar API na importação/startup. Modelo vem de GEMINI_MODEL; chave de GEMINI_API_KEY, nunca frontend.
Implementar prompts/01-extract.md e prompts/02-map-fhir.md como rascunhos fornecidos pelo orquestrador; retorno JSON em ambos. Etapa 1 extrai fatos/evidências; etapa 2 mapeia fatos em FHIR. Não inserir dados de exemplos no paciente real.
Duas chamadas Gemini no máximo por documento, saída limitada (ex.8192 tokens por etapa), sem auto-repair ou loop; sem truncamento silencioso. Temperatura baixa quando o modelo configurado permitir. Não pesquisar web por documento nem enviar o guia/folder inteiro.
Validar JSON parseado e Bundle localmente ANTES de marcar ready/persistir resultado bem-sucedido.
Validação mínima: resourceType Bundle; tipo collection ou document; entry não vazio; cada recurso com resourceType/id válidos e únicos; fullUrl único; referências internas resolvidas por fullUrl ou ResourceType/id; campos base obrigatórios dos recursos efetivamente emitidos. Document exige Composition primeira e seus campos obrigatórios/referências. Não reparar referência quebrada copiando outro paciente.
validation_level=structural; aviso na UI: "Validação estrutural do protótipo; conformidade BR Core ainda não verificada." Não confundir JSON parseável com conformidade BR Core ou correção clínica.
docs/FHIR_SCOPE.md delimita versão e pendências. Não declarar meta.profile conforme sem validação apropriada.

## Chamada real e revisão do prompt
O documento original exige revisão do prompt por Marcos. Não bloquear a implementação por isso.
Criar ENABLE_REAL_GOOGLE=false e FHIR_PROMPT_APPROVED=false no .env.example, preservando .env existente. Com adaptadores reais, chamar Google somente com flags verdadeiras e credenciais configuradas. Fakes injetados de teste independem dessas flags.
Não ativar flags nem executar chamadas reais nesta tarefa antes de revisar os prompts. Preparar um comando de smoke de documento sintético, limitado a 1 página e no máximo 1 Vision + 2 Gemini, sem retries; não executar ainda.
O orquestrador não conseguiu extrair o PDF do estudo pelo conector: se for necessário para fundamentação, extrair localmente apenas título/metodologia de prompting para docs/STUDY_NOTES.md (até 300 palavras com páginas). Não afirmar que técnica foi comprovada no estudo sem leitura. Não reescrever prompts extensos por conta própria.
Ao publicar, indicar prompts prontos para revisão e eventual falta de credenciais como pendências específicas, não como ausência de implementação.

## Interface mínima
Servir no mesmo FastAPI: HTML/JS + Tailwind, sem SPA. Tela login com contas demo e dashboard após sessão. fetch com credentials same-origin; sem localStorage de token.
Upload PDF/JPEG, tipo Texto, progresso/status via polling GET (2 s enquanto houver pendência), lista, renomear e baixar JSON. Evitar polling quando não há pendentes; nunca chamar conversão no polling.
Usar logo/cores do repo, todos os textos pt-BR. Mostrar falhas e aviso de validação; não inserir texto de documentos como HTML não sanitizado.
Não inventar termos LGPD/consentimento, não chamar tela de produção. Pastas, imagens médicas, PDF e compartilhamento ficam explicitamente para depois.
CSS Tailwind pode ser compilado localmente com ferramentas existentes; não introduzir bundler/framework.

## Aceite e handoff
Testes fornecidos: tests/test_documents.py (5 casos) + regressões auth/health. tests/__init__.py permite reutilizar fixtures sem copiá-las.
Atualizar scripts/run_tests.py já preparado pelo orquestrador para rodar os 11 testes. Não alterar os testes para passar.
Executar migração local e runner; não recriar os bancos. Node --check no JS quando disponível. Descrever caminhada manual da tela se não houver automação de navegador.
Se o mesmo erro persistir após duas tentativas relevantes, registrar causa concreta; seguir partes independentes.
Relatório docs/reviews/03-core-flow.md até 250 palavras: arquivos, comandos/resultados, teste UI feito/não feito, integração real feita/não feita, pendências de prompt/credenciais.
Atualizar docs/STATUS.md, revisar staged diff e fazer commit/push normal em dev/foundation. Nenhum segredo/dado real. Não fazer deploy/merge e não iniciar funcionalidades adiadas.
