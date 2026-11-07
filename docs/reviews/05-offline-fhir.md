# Revisão offline dos exemplos Gemini-only
Data: 07/11/2026.

## Resultado técnico
Os três bundles normalizados passaram na validação estrutural local, sem nova inferência. Arquivos em demo-results/gemini-only-normalized/. Originais preservados.
ClinicalImpression é adequado para a avaliação clínica já documentada no manuscrito. Acrescentado suporte com status permitido e subject para Patient/Group, mantendo referências internas verificadas.
Fonte: https://hl7.org/fhir/R4/clinicalimpression.html.

Também foram encontrados URNs com caracteres não hexadecimais e IDs reutilizados entre saídas. O backend agora gera IDs técnicos por documento e reescreve referências. Corrigidos dois aliases legados dos sistemas CPF/CNS; valores dos identificadores e dados clínicos não foram completados nem alterados.

## Fidelidade: ainda incompleta
Comparação das transcrições e saídas; o manuscrito original também foi inspecionado visualmente.
- PDF: preservou paciente, alergia, condição, medicamento e três exames, mas faltam frequência da medicação, conduta de ajuste 25 -> 50 mg, vacinas, sexo e autoria/instituição presentes na transcrição.
- Receita: medicamento, quantidade 60 e instrução noturna preservados; endereço transcrito não foi mapeado.
- Manuscrito: "crise constante" foi parafraseado como "dor constante"; nem todos os dados demográficos/institucionais foram mapeados. A representação da queixa como Condition e seus estados precisa de revisão sem assumir diagnóstico confirmado.
Prompts ajustados para futuras conversões, sem repetir inferência para testar esses ajustes. Não declarar fidelidade clínica ou conformidade completa BR Core.

## Verificação
Mesmos cinco métodos de regressão, com novas verificações de ClinicalImpression/UUID/referências: aprovados com SDK simulado. Validação offline dos três artefatos normalizados: aprovada. Nenhum novo teste PostgreSQL/Windows ou chamada Google nesta revisão.

## Atualizar o ledger local
Após sincronizar dev/foundation:
```powershell
.\.venv\Scripts\python.exe scripts/revalidate_saved.py
```
Reutiliza candidatos salvos, atualiza ledger e preserva histórico. Não modifica banco ou candidatos originais. Não usar --retry-failed para resolver este erro estrutural.
Imagens médicas e revisão de fidelidade permanecem pendentes.
