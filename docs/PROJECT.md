# SAÚVA — escopo consolidado

Fonte: agent-files/SAUVA_ORCH_PROMPT.docx e decisões posteriores do Marcos em 07/11/2026. Este resumo não implementa decisões pendentes.

## Confirmado
- Protótipo web brasileiro: funcionários administrativos/provedores organizam documentos de pacientes. Não presumir que usuário autenticado seja o paciente do registro.
- FastAPI + PostgreSQL + HTML/JS/Tailwind. Drive por usuário: uploads, nomes, pastas, listagem, JSON/PDF e compartilhamento.
- Formatos iniciais PDF e JPEG. Rótulos: Texto e Exame de imagem.
- Atualização aprovada: somente Gemini Developer API. JPEG e PDF digitalizado/misto usam leitura multimodal Gemini para transcrição/fatos em uma chamada, depois mapeamento FHIR em outra. PDF totalmente textual usa extração local. Cloud Vision e suas credenciais não são necessários.
- Texto extraído -> Gemini -> bundle FHIR orientado por BR Core. Não inventar achados ausentes.
- Exames de imagem são imagens médicas reais, não apenas laudos. Interpretação automática ainda NÃO foi autorizada como decisão clínica/produto.
- Fechamento por prazo: exportação FHIR/transcrição -> PDF local determinístico, sem outra inferência. Template provisório; template do Marcos pendente. Não integrar Bahmni/fhir-pdf.
- GPT/Codex para desenvolvimento; somente Gemini no runtime de IA do produto.
- Fechamento por prazo: destinatário registrado, um documento, link/senha com resgate único e expiração de 24h. Resgate abre sessão restrita de 10min para abrir, visualizar e baixar. Cinco senhas incorretas bloqueiam link. Sem envio automático.
- Marcos autorizou os prompts atuais para teste limitado com os exemplos fictícios; validação clínica/BR Core completa permanece pendente.
- Testes definidos pelo orquestrador, no máximo cinco por tarefa, mais integração apropriada.
- Marcos confirmou contas de demonstração pré-criadas em vez de autocadastro.
- Entrega prioritária: Texto PDF/JPEG até 10 MB e 10 páginas, originais em uploads/ por usuário e processamento serial com status. Fechamento 06 acrescenta pastas planas, anexos de imagens médicas, PDF local e compartilhamento.
- Tarefa 03 implementa o caminho completo com testes simulados e adaptadores reais preparados. O prompt continua sujeito à revisão anterior à primeira chamada real.

## Materiais
- agent-files/Bundle-fhir-brcore-example.json
- agent-files/fhir-brcore-examples/
- agent-files/FHIR-CONVERSION-STUDY.pdf
- agent-files/style-guidelines.md
- agent-files/sauva-logo.svg
- Guia oficial indicado: https://hl7.org.br/fhir/core/index.html

Não enviar toda a pasta de exemplos para cada inferência. O orquestrador selecionará exemplos mínimos e pertinentes. O bundle principal contém múltiplos pacientes; não assumir que primeiro Patient seja o sujeito do documento.

## Decisões para as respectivas tarefas
1. Auth: comportamento aprovado: duas contas demo com mesmas permissões, email/senha, cookie de sessão de 8 horas, logout com revogação, sem autocadastro ou recuperação de senha. Posicionamento e texto do consentimento ficam para a interface. A política de senha não deve bloquear login de uma senha existente apenas por regra de cadastro.
2. Arquivos: aprovados 10 MB/10 páginas, uploads/ local por proprietário, originais mantidos para demonstração e processamento serial. PDFs mistos e inválidos especificados na tarefa 03.
3. FHIR: versão/pacote BR Core, recursos mínimos por tipo, validação estrutural e de perfil, tratamento de informações ausentes.
4. Imagem: fechamento usa DocumentReference com anexo original PDF/JPEG e PDF visual; sem inventar paciente nem diagnóstico. DICOM/interpretação fora do protótipo.
5. Compartilhamento: fechamento usa resgate único seguido de sessão de 10min restrita ao destinatário/documento, com downloads durante esse período.
6. PDF: fechamento usa template local provisório; dados ausentes não são completados. Modelo personalizado fica para depois.
7. Conversão: execução síncrona ou processamento em segundo plano com status; limites e repetição/custo.

Credenciais não são pré-requisito da fundação. Antes de smoke tests reais: GEMINI_API_KEY e GEMINI_MODEL configurados para Gemini Developer API; banco local para uso da aplicação. Não requer Vision, ADC ou faturamento Vision. Não expor valores ao orquestrador.
