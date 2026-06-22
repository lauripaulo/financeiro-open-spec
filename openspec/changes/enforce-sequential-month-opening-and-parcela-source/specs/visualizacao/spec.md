# Delta para Visualizacao

## REQUISITOS ADICIONADOS

### Requirement: Feedback explicito para tentativa de abertura de mes fora da sequencia
Quando o usuario tentar abrir um mes fora da sequencia permitida, o sistema SHALL
informar de forma explicita qual e o mes/ano permitido naquele momento e SHALL
orientar a abertura desse mes permitido.

#### Scenario: Usuario tenta abrir mes diferente do permitido
- GIVEN o ultimo mes aberto e abril/2026
- WHEN o usuario tenta abrir junho/2026
- THEN o sistema SHALL informar que maio/2026 e o mes permitido
- AND SHALL exibir acao para abrir o mes permitido

#### Scenario: Usuario tenta criar primeiro mes diferente do atual
- GIVEN nao existe nenhum mes aberto
- WHEN o usuario tenta abrir um primeiro mes diferente do mes atual
- THEN o sistema SHALL informar que somente o mes atual pode ser aberto primeiro
