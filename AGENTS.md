# SAÚVA — instruções para o agente local

Produto brasileiro para registros de saúde; interface, mensagens ao usuário e documentação operacional em pt-BR. Backend FastAPI/Python; frontend HTML/JS/Tailwind; PostgreSQL. Desenvolvimento local em Windows, 8 GB RAM.

## Execução
- Leia este arquivo, docs/PROJECT.md, docs/STATUS.md e SOMENTE a tarefa solicitada. Abra outros arquivos apenas quando a tarefa apontar ou o código exigir.
- Execute somente as tarefas explicitamente solicitadas, respeitando dependências. Não implemente o restante do roadmap.
- Antes de uma decisão de produto ou arquitetura não resolvida, pare a parte dependente e pergunte ao Marcos. Informe a alternativa recomendada e seu efeito. Correções locais e detalhes mecânicos dentro da tarefa podem prosseguir.
- Preserve agent-files/ como material de referência. Não suponha que exemplos sejam bundles clinicamente coerentes ou validados.
- O orquestrador define testes e critérios; execute os testes fornecidos. Não altere testes para acomodar falhas, nem invente novos testes/contratos sem apresentar a necessidade.
- Não crie subagentes. Não substitua alterações do usuário. Deploy, merge e force-push não autorizados.
- Handoff aprovado: commits e push normal de arquivos revisados da tarefa para dev/foundation estão autorizados, incluindo checkpoint da fundação 01. Use allowlist e revise staged diff. O orquestrador publica tarefas; o agente local publica código e relatório; pare ao final para revisão.
- Se uma tarefa antiga proibir commit/push, a autorização explícita de handoff na tarefa atual prevalece para seus arquivos e checkpoint. Nunca inclua .env, credenciais, bancos ou material desconhecido.

## Economia de contexto e chamadas
- Use rg para localizar símbolos e leia trechos relevantes. Não despeje o repositório, lockfiles, SVGs, bundles completos ou PDFs no contexto.
- Não leia DOCX/PDF em toda tarefa. O resumo em docs/PROJECT.md atende à fundação; extração seletiva do estudo será tarefa do orquestrador.
- Consulte documentação oficial somente para a dúvida concreta; evite pesquisa repetida.
- Não faça chamadas Gemini/Vision em testes rotineiros. Use adaptadores simulados; chamadas reais exigem tarefa explícita e orçamento.
- Instale apenas dependências necessárias à tarefa; reutilize o ambiente e as ferramentas existentes.
- Se o mesmo erro persistir após duas tentativas relevantes, apresente a causa provável e o bloqueio; não entre em loop.
- Mantenha docs/STATUS.md curto: tarefa, alterações, verificação, bloqueios e próxima ação. Não copie conversas.
- Ao terminar: resumo de até 200 palavras, arquivos modificados, comandos de verificação e resultados, decisões pendentes. Nunca inclua segredos ou dados clínicos reais.

## Segurança básica do protótipo
- .env, credenciais, banco, uploads, PDFs gerados e logs privados fora do Git; .env.example somente com placeholders.
- Chaves Google são configurações do servidor, nunca conteúdo do frontend nem campos de credenciais por paciente.
- Senhas devem ser armazenadas como hashes apropriados, não texto ou criptografia reversível.
- Usar dados sintéticos no desenvolvimento. Identificadores e mensagens não devem vazar registros de outros usuários.
