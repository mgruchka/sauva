# Gemini-only — execução local dos exemplos

Marcos aprovou substituir Cloud Vision pelo Gemini em 07/11/2026. Não ativar faturamento Vision, não configurar ADC, não criar chave de serviço para este fluxo. Somente GEMINI_API_KEY e GEMINI_MODEL do Gemini Developer API são necessários para conversão.

## Caminho
- PDF com texto em todas as páginas: extração local -> fatos Gemini -> FHIR Gemini.
- PDF digitalizado/misto: PDF completo enviado uma vez ao Gemini para transcrição + fatos -> FHIR Gemini.
- JPEG Texto: JPEG enviado ao Gemini para transcrição + fatos -> FHIR Gemini.
- No máximo duas chamadas por documento, sem retries; não há chamada Cloud Vision. O cliente força vertexai=False.
- Exame de imagem/radiografia continua pendente. A mudança de OCR não implementa interpretação diagnóstica.

## Configuração
Preservar .env existente. GEMINI_API_KEY deve ser a chave atual de AI Studio; GEMINI_MODEL é o identificador do modelo, não nome/número do projeto.
As variáveis GOOGLE_APPLICATION_CREDENTIALS e GOOGLE_CLOUD_PROJECT são ignoradas por este caminho. Não é necessário apagar suas credenciais.
O script dos exemplos ativa as duas flags só no próprio processo, com base na autorização já dada. Para a interface web, definir ENABLE_REAL_GOOGLE=true e FHIR_PROMPT_APPROVED=true localmente e reiniciar o servidor.
Conta/modelo Gemini continua sujeito às cotas do free tier; não há promessa de cota ilimitada. Não habilitar billing para resolver erro de cota neste teste.

## Rodar
Sincronizar com origin/dev/foundation preservando alterações locais.
Nenhuma dependência nova foi adicionada; google-cloud-vision saiu de requirements.txt. Não é necessário recriar .venv ou remover pacotes instalados à força.
Verificações pertinentes à mudança (sem reimplementar auth):
```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_documents.py tests/test_review03.py tests/test_health.py -q
.\.venv\Scripts\python.exe scripts/validate_demo_files.py
```
O primeiro comando tem onze testes relevantes. O segundo realiza os três exemplos de texto, até seis chamadas Gemini, zero Vision.
Para iniciar por apenas um:
```powershell
.\.venv\Scripts\python.exe scripts/validate_demo_files.py --file example_text.pdf
```

Ledger novo em generated/demo-gemini/report.json; o antigo erro Vision em generated/demo-validation/ foi preservado e não bloqueia esta tentativa Gemini.
Arquivo já tentado não é repetido automaticamente. Em falha, imprime erro com chave/segredos removidos e interrompe os próximos arquivos. Não trocar de modelo/reativar cobrança/repetir sozinho.
Depois de corrigir a causa, uma tentativa dirigida e explícita:
```powershell
.\.venv\Scripts\python.exe scripts/validate_demo_files.py --retry-failed example_text.pdf
```
Não usar retry sem diagnóstico. Retry guarda histórico e executa apenas esse arquivo.

O script espaça chamadas em 15 s por padrão para reduzir risco de limite de frequência, configurável com GEMINI_MIN_INTERVAL_SECONDS. Isso não garante que toda cota esteja disponível.
Saídas incluem texto extraído e candidate.json ANTES da validação; se FHIR estrutural falhar, revisar o candidato sem pagar nova inferência desnecessariamente.

## Handoff
O agente local só precisa executar, não refatorar: rodar os onze testes pertinentes, depois exemplos se passarem; publicar resumo em docs/reviews/04-gemini-demo.md com resultados reais, nomes de arquivos e erro sanitizado se houver. Não repetir chamadas em caso de falha.
Os exemplos foram declarados fictícios por Marcos. Para revisão pelo GitHub, pode copiar os .fhir.json ou .candidate.json e .extracted.txt produzidos APENAS desses três exemplos para demo-results/gemini-only/, sem arquivos .env/credenciais. Commit/push normal em dev/foundation autorizados.
Validação estrutural não prova fidelidade ao documento nem conformidade BR Core completa. Conferir manualmente dados, ausências, negações e medicamentos. Sem deploy/merge.
