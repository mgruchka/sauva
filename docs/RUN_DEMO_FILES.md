# Rodada real com exemplos do repositório
Marcos autorizou em 07/11/2026 os exemplos de demo-files/. Execução direta no terminal, sem outra rodada de geração de código.
Não executar scripts/smoke_google.py nesta rodada: esse script usa outro documento sintético.

Arquivos confirmados:
- example_text.pdf: duas páginas sem texto extraível, logo OCR PDF, não caminho PDF textual.
- example_text-1.jpeg e example_text-2.jpeg: OCR JPEG.
- example_imaging.jpeg: radiografia; pipeline Exame de imagem ainda não implementado. Não enviar como Texto nem apresentar como aprovado.

Limite desta rodada: três arquivos serialmente, no máximo quatro chamadas Vision e seis Gemini no total. Sem retentativas automáticas. Erro no primeiro arquivo interrompe antes de cobrar os seguintes.
O script ativa as flags somente no próprio processo para os exemplos explicitamente solicitados. Não modifica .env nem muda o servidor. Usa GEMINI_API_KEY/GEMINI_MODEL e autenticação Vision (ADC ou arquivo configurado) já presentes localmente; não mostra valores.
Se faltarem configurações, informar os nomes ausentes; não inventar modelo nem pedir chaves pelo chat.

PowerShell na raiz, com alterações locais já publicadas:
```powershell
git pull --ff-only origin dev/foundation
.\.venv\Scripts\python.exe scripts/validate_demo_files.py
```

Resultados e ledger em generated/demo-validation/, ignorados pelo Git. A entrada do arquivo é gravada ANTES das chamadas. Reexecutar o comando pula arquivos já registrados, inclusive falhos; não apagar o ledger para tentar de novo sem diagnóstico. A execução exige um terminal por vez, não rodar cópias paralelas.

Esta rodada exercita extração -> OCR -> Gemini -> validador diretamente, sem servidor, autenticação ou banco. Estes últimos já têm testes simulados/integrados; não alegar que este script testou upload/UI.
Conferir o JSON e extracted.txt lado a lado com os originais: nomes/identificadores, negações, datas, medicamentos/doses/via/frequência, omissões e informação inventada. Não contar JSON parseável como fidelidade ou conformidade BR Core.

Para review GitHub: o agente pode publicar somente resumo de report.json em docs/reviews/04-demo-results.md, sem credenciais. Extratos/JSON ficam locais até revisão do conteúdo; não é necessário rodar de novo os 16 testes nesta etapa.
Imagens médicas exigem próxima tarefa própria; decidir preservar/anexar metadados versus interpretação antes da implementação.
