# Estado

- Fluxo Gemini-only sincronizado e verificado localmente, sem Cloud Vision.
- Testes: chamada direta do pytest encontrou 5 erros de setup por `.env` não carregado; com `load_dotenv` antes dos mesmos arquivos, **11 passed, 7 subtests passed in 11.52s**.
- Exemplos reais: `example_text.pdf` e `example_text-1.jpeg` geraram JSON com validação estrutural; `example_text-2.jpeg` falhou em `ValueError: Tipo de recurso inválido.` O candidato contém `ClinicalImpression`, fora de `SUPPORTED_TYPES`. Sem retry; zero chamadas Vision. Radiografia segue pendente.
- Resultados publicáveis em `demo-results/gemini-only/`; ledger e saídas completas permanecem em `generated/demo-gemini/` fora do Git. Fidelidade clínica e BR Core não verificados.
- Próxima ação: revisão do candidato e decisão sobre `ClinicalImpression` versus mapeamento para recurso suportado. Não executar inferência adicional sem essa decisão.
