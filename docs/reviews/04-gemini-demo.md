# Gemini-only — resultados locais

Sincronizado `dev/foundation`; nenhuma refatoração nesta rodada. O pytest direto não carregou `.env`: 6 passaram e 5 tiveram erro de setup por `TEST_DATABASE_URL` ausente no processo. Com `load_dotenv('.env')` antes dos mesmos testes: **11 passed, 7 subtests passed in 11.52s**.

`scripts/validate_demo_files.py` foi executado uma vez, sem retries e sem Vision. `example_text.pdf` e `example_text-1.jpeg` produziram Bundle JSON com validação estrutural. `example_text-2.jpeg` produziu texto extraído e candidato JSON, mas falhou na validação local: `ValueError: Tipo de recurso inválido.` O candidato contém `ClinicalImpression`, fora do subconjunto `SUPPORTED_TYPES`; não é falha de autenticação ou cota. O script interrompeu a sequência. `example_imaging.jpeg` segue sem pipeline.

Publicados em `demo-results/gemini-only/`: os dois `.fhir.json` aprovados estruturalmente, seus `.extracted.txt`, e o `.candidate.json` e `.extracted.txt` do terceiro exemplo. `generated/demo-gemini/report.json` permanece local e não foi apagado. Os arquivos foram declarados fictícios por Marcos; não foi feita revisão de fidelidade clínica, negações ou conformidade BR Core.

Próxima decisão: revisar o candidato `ClinicalImpression` e decidir se esse recurso entra no escopo/validação ou se o prompt deve emitir recurso suportado. Não repetir inferência até essa decisão.
