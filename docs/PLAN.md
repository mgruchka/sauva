# Plano incremental

Rodar uma tarefa de cada vez. Tarefas 00 e 01 estão prontas; demais linhas são roadmap, não autorização para implementar decisões pendentes.

| Etapa | Entrega | Dependência / decisão antes de detalhar |
|---|---|---|
| 00 | Inspeção local sem mutação | Git, Python, Codex; Google/banco podem estar pendentes |
| 01 | Fundação FastAPI offline + health + execução local | 00 sem bloqueio de ambiente |
| 02 | Auth e banco/migrações | Confirmar cadastro, identidade e sessão |
| 03 | Upload, nomes, pastas e isolamento por proprietário | 02; limites, armazenamento e modelo de processamento |
| 04 | Extração PDF/JPEG e OCR por adaptador | 03; PDFs mistos, mocks e tratamento de falhas |
| 05 | Prompt e contrato FHIR revisados | Orquestrador extrai estudo e exemplos; Marcos aprova prompt |
| 06 | Gemini texto -> FHIR, validação e persistência | 04/05; smoke test real explicitamente delimitado |
| 07 | Imagens médicas | Resolver representação e interpretação antes da implementação |
| 08 | Dashboard e ações em pt-BR | APIs estabilizadas; guidelines/logo apenas nesta etapa |
| 09 | Gemini -> conteúdo de relatório -> PDF | Template do Marcos e contrato de imagens |
| 10 | Link de compartilhamento e resgate atômico | Regra de sessão confirmada; testes concorrentes essenciais |
| 11 | Integração e roteiro da demonstração | Fluxo completo com dados sintéticos |

## Estratégia de economia
Primeiro caminho vertical: iniciar servidor -> health -> auth -> um upload de texto -> conversão -> listar -> baixar JSON.
Completar depois pastas, imagens, PDF e compartilhamento. Isso ordena a entrega sem remover funcionalidades do escopo.
Dependências externas simuladas até o fluxo estar pronto. Uma conversão por documento; não repetir conversão ao listar/renomear/baixar JSON. Estratégia de cache de PDF será definida com a tarefa 09.
Cada tarefa recebe arquivos relevantes, contrato, testes prescritos, comando e condição de parada.
Revisões usam diff e resultado resumido, não transcrições extensas. Nova sessão por módulo após checkpoint aprovado; não por cada comando.
