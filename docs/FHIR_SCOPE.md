# Escopo FHIR da entrega 03
O guia oficial consultado em 07/11/2026 identifica FHIR R4 4.0.1 e pacote br.gov.saude.br-core.fhir#1.5.1.
Fontes: https://hl7.org.br/fhir/core/index.html e https://hl7.org.br/fhir/core/StructureDefinition-br-core-patient.html.

Esta entrega implementa validação estrutural do bundle e suas referências. Não implementa validação completa de perfis/terminologias BR Core nem verificação clínica.
Não adicionar meta.profile como certificado de conformidade. Ausência de CNS/CPF não autoriza inventá-los para satisfazer um perfil.

O exemplo principal do repo contém múltiplos pacientes: Composition.subject aponta para um Patient e uma Condition.subject para outro. Não é um exemplo clínico coerente a ser copiado integralmente. Preservar o material como referência e usar somente exemplos mínimos selecionados.
Os prompts fornecidos são rascunhos do orquestrador, aguardando revisão do Marcos e confronto com o estudo. O PDF do estudo não foi lido nesta rodada por indisponibilidade do acesso binário no conector.

Antes da conversão real: revisar os dois prompts; selecionar o exemplo de demonstração e recursos emitidos; registrar limites da validação. Duas etapas/few-shot/temperatura baixa vêm da solicitação original, não de uma conclusão atribuída ao estudo ainda não lido.
Não travar armazenamento/OCR/SDK/UI/testes por essa revisão; manter a chamada real desligada até a revisão.
