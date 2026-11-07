# 00 — conferir ambiente local

Leia AGENTS.md, docs/PROJECT.md e docs/STATUS.md. Não leia agent-files/. Não modifique instalação, configurações, banco ou código nesta etapa.

## Inspeção
1. Verifique diretório, git status --short e branch. Não mude branch sobre alterações locais. O esperado é mgruchka/sauva, branch dev/foundation.
2. Identifique Python com py -0p no Windows (ou equivalente). Informe versão e caminho, sem inspecionar ambientes alheios. Use esse intérprete explicitamente no projeto.
3. Confira git --version, node --version e npm.cmd --version quando disponíveis. Node não é requisito da tarefa 01.
4. Confira se psql e gcloud estão disponíveis, sem executar chamadas pagas ou inicializações. Ausência é pendência futura.
5. Informe somente presença/ausência das variáveis GEMINI_API_KEY e GOOGLE_APPLICATION_CREDENTIALS. Não imprima valores, .env, tokens, auth.json nem credenciais. Credenciais ADC podem existir sem variável; não leia seu conteúdo.
6. Liste pendências em até 150 palavras. Não instale ferramentas automaticamente.

## Aceite / parada
Python e Git presentes + repositório correto permitem 01. Google/PostgreSQL podem continuar pendentes.
Se houver mudanças locais conflitantes, intérprete ausente ou dúvida de diretório, pare e informe. Não crie testes desta inspeção.
