# Revisão e primeiro smoke — 03

## Resultado da revisão
O worker reportou 11 testes de integração aprovados. O orquestrador revisou fontes de 1f4a838 e reproduziu dois defeitos: prescrição com medicationReference rejeitada e resourceType inventado aceito.
Corrigiu o validador para suportar a escolha medication[x] e limitar tipos ao subconjunto clínico documentado no código.
Adaptadores agora têm timeout explícito (Vision 30 s, Gemini 60 s por chamada), retries desativados, fechamento dos clientes e interrupção quando a resposta é truncada/bloqueada ou sem fatos. Texto acima de 60.000 caracteres é rejeitado antes da inferência, sem corte silencioso.
Instruções e dados são enviados separadamente ao Gemini.

O orquestrador executou cinco regressões stdlib sem rede/Google/banco: 5 aprovadas. Isso não valida compatibilidade do SDK instalado, Windows, PostgreSQL ou comportamento de um modelo real.
Testes originais preservados; runner inclui agora 16 testes. Reexecutar localmente por haver alterações novas. Não recriar ambiente, repetir migração ou refazer funcionalidades.
Caminhada manual da UI ainda pendente. Stage interno aparece em inglês e Tailwind usa CDN; esses detalhes não bloqueiam este smoke local.

## Executar sem gastar uma rodada do agente
Na raiz do projeto, com trabalho já publicado:
```powershell
git pull --ff-only origin dev/foundation
.\.venv\Scripts\python.exe scripts/run_tests.py
```

## Antes de chamar Google
Marcos precisa aprovar prompts/01-extract.md e prompts/02-map-fhir.md. Eles fazem extração de fatos/evidências e mapeamento FHIR sem completar dados ausentes; permitem collection quando faltam requisitos de document. Não são validação completa BR Core, nem tiveram ainda fundamentação conferida contra o PDF do estudo.
Não ativar flags ou executar smoke antes dessa aprovação. Não gerar/usar dados reais.

Após aprovação, configurar localmente GEMINI_API_KEY e GEMINI_MODEL e as flags ENABLE_REAL_GOOGLE=true, FHIR_PROMPT_APPROVED=true. Manter credenciais fora do Git. Reiniciar o servidor: as variáveis .env são carregadas na inicialização.
Primeiro terminal:
```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
```
Segundo terminal:
```powershell
.\.venv\Scripts\python.exe scripts/smoke_google.py
```
O script cria uma página sintética textual e faz somente um upload (zero OCR Vision; no máximo duas chamadas Gemini). Não repetir em caso de erro sem diagnóstico. Se esgotar a espera, o job pode continuar no servidor; não reenviar.
Em sucesso, abrir a interface, baixar JSON e conferir manualmente que há somente fatos sintéticos documentados, sem CPF/CNS/data/autoria inventados. Publicar relatório curto com resultados e pendências, sem chaves ou senhas.
