# Estado
- Gemini-only executado localmente pelo worker: dois documentos passaram no validador anterior; o terceiro produziu candidato bloqueado por ClinicalImpression. Nenhum retry Vision.
- Revisão do orquestrador: ClinicalImpression suportado com campos/referências verificados; UUIDs e dois aliases CPF/CNS normalizados no backend, sem alterar valores clínicos.
- Três artefatos normalizados validados offline em demo-results/gemini-only-normalized/, sem chamada Google adicional. Cinco regressões com SDK simulado passaram; quantidade de testes existentes mantida.
- Fidelidade ainda parcial: faltam campos estruturados em relação às transcrições e há paráfrase no manuscrito. Ver docs/reviews/05-offline-fhir.md.
- Próxima ação local: sincronizar e executar scripts/revalidate_saved.py para atualizar ledger sem nova inferência. Não precisa repetir os testes Gemini.
- Novos prompts melhoram preservação de dados, mas não foram reavaliados por nova chamada real. Conformidade completa BR Core e imagens médicas continuam pendentes.
