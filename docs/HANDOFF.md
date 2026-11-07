# Comunicação GitHub — SAÚVA

Marcos aprovou o fluxo: orquestrador publica tarefas/testes; Codex local implementa e publica código/relatório em dev/foundation; Marcos avisa "pronto para revisão"; orquestrador lê pelo GitHub.

## Fluxo por tarefa
1. Preservar alterações locais com checkpoint seletivo quando pertencem à tarefa; sincronizar remoto sem descarte/force-push.
2. Ler AGENTS.md e a tarefa indicada, sem carregar referências não solicitadas.
3. Executar só a tarefa indicada e seus testes. Se bloqueado, relatar exatamente o que não foi verificado.
4. Escrever docs/reviews/<id>-<nome>.md: até 250 palavras, resumo, arquivos, testes/comandos/resultados, bloqueios. Não incluir segredos nem transcrições.
5. Revisar staged diff e publicar commit/push normal em dev/foundation. Parar; revisão do orquestrador precede a próxima tarefa.
6. Informar a Marcos apenas estado e SHA. Ele não precisa copiar código para o chat.

Somente esta branch de desenvolvimento está autorizada. Não fazer merge em main, deploy ou iniciar outras tarefas. Credenciais ficam locais.
