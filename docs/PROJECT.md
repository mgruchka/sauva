# SAÚVA — escopo consolidado

Fonte: agent-files/SAUVA_ORCH_PROMPT.docx e decisões posteriores do Marcos em 07/11/2026. Este resumo não implementa decisões pendentes.

## Confirmado
- Protótipo web brasileiro: funcionários administrativos/provedores organizam documentos de pacientes. Não presumir que usuário autenticado seja o paciente do registro.
- FastAPI + PostgreSQL + HTML/JS/Tailwind. Drive por usuário: uploads, nomes, pastas, listagem, JSON/PDF e compartilhamento.
- Formatos iniciais PDF e JPEG. Rótulos: Texto e Exame de imagem.
- Texto em JPEG e PDFs digitalizados passam por OCR Cloud Vision. PDFs com texto extraível usam extração local; PDFs mistos precisam de tratamento por página.
- Texto extraído -> Gemini -> bundle FHIR orientado por BR Core. Não inventar achados ausentes.
- Exames de imagem são imagens médicas reais, não apenas laudos. Interpretação automática ainda NÃO foi autorizada como decisão clínica/produto.
- Exportação FHIR -> conteúdo estruturado por Gemini -> PDF renderizado pelo backend. Template do Marcos pendente. Não integrar Bahmni/fhir-pdf.
- GPT/Codex para desenvolvimento; Gemini/Vision continuam no runtime do produto.
- Compartilhamento: destinatário registrado, um documento, credencial de uso único e expiração de 24 h. Usuário quer abrir, visualizar e baixar. Duração e encerramento da sessão de acesso ainda precisam de definição.
- Prompt de conversão precisa de revisão do Marcos antes de uso no pipeline real.
- Testes definidos pelo orquestrador, no máximo cinco por tarefa, mais integração apropriada.
- Marcos confirmou contas de demonstração pré-criadas em vez de autocadastro.

## Materiais
- agent-files/Bundle-fhir-brcore-example.json
- agent-files/fhir-brcore-examples/
- agent-files/FHIR-CONVERSION-STUDY.pdf
- agent-files/style-guidelines.md
- agent-files/sauva-logo.svg
- Guia oficial indicado: https://hl7.org.br/fhir/core/index.html

Não enviar toda a pasta de exemplos para cada inferência. O orquestrador selecionará exemplos mínimos e pertinentes. O bundle principal contém múltiplos pacientes; não assumir que primeiro Patient seja o sujeito do documento.

## Decisões para as respectivas tarefas
1. Auth: contas demo confirmadas; email versus username, sessão e desenho da tarefa 02 ainda sujeitos à confirmação; posicionamento e texto do consentimento. A política de senha não deve bloquear login de uma senha existente apenas por regra de cadastro.
2. Arquivos: limites de tamanho/páginas e retenção dos originais; local de armazenamento. PDFs mistos e arquivos inválidos.
3. FHIR: versão/pacote BR Core, recursos mínimos por tipo, validação estrutural e de perfil, tratamento de informações ausentes.
4. Imagem: preservar/anexar apenas ou interpretar; associação ao paciente; representação e obtenção da imagem no PDF. Não desenvolver diagnóstico automaticamente.
5. Compartilhamento: momento de resgate, duração da sessão e regra de download. Proposta ainda não confirmada: resgate único abre sessão temporária restrita ao documento, com download durante a sessão.
6. PDF: receber template, formato da resposta Gemini, tratamento de campos ausentes e imagens.
7. Conversão: execução síncrona ou processamento em segundo plano com status; limites e repetição/custo.

Credenciais não são pré-requisito da fundação. Antes de smoke tests reais: projeto Google, Vision habilitado e faturamento, autenticação local configurada, GEMINI_API_KEY e modelo configurado, banco local. Não expor valores ao orquestrador.
