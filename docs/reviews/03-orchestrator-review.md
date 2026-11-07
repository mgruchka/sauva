# Revisão do orquestrador — 03
Fontes revisadas no commit 1f4a838fbd931d428e49120cb24a7f43881c3949. Worker reportou 11 testes aprovados, sem chamada Google ou caminhada UI.

Defeitos reproduzidos e corrigidos: MedicationRequest com medicationReference válida rejeitada; tipo de recurso inexistente aceito. Adaptadores corrigidos para timeout/retries explícitos, fechamento de clientes e rejeição de resposta interrompida/sem fatos; instruções Gemini separadas dos dados.

Verificação executada pelo orquestrador: cinco testes stdlib com SDKs simulados, sem rede/banco, todos aprovados. Sintaxe do smoke verificada; script real NÃO executado. Não houve teste contra os SDKs instalados nem nova execução PostgreSQL/Windows.

Testes originais preservados; scripts/run_tests.py agora inclui 16 testes. Reexecutar localmente. docs/REVIEW03_SMOKE.md explica sincronização, revisão dos prompts e primeiro smoke de uma página sintética, com até duas chamadas Gemini e nenhuma Vision.

Estado: caminho implementado; aguardar regressão local pós-correção e aprovação do prompt antes do smoke. Sem conformidade BR Core ou correção clínica certificadas. Nenhum deploy/merge ou chamada paga.
