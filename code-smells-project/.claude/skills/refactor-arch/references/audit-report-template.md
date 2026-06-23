# Template do Relatório de Auditoria (saída da Fase 2)

Este arquivo define a formatação **exata** de cada saída de fase. O relatório da Fase 2 salvo em `reports/audit-project-{N}.md` deve ser byte-a-byte igual ao impresso na tela.

Markdown é o formato canônico. Envolver os blocos de moldura (`===`) em texto puro para que renderizem igual na tela e no `.md` salvo.

---

## Bloco da Fase 1 (impresso antes da auditoria)

```
================================
FASE 1: ANÁLISE DO PROJETO
================================
Linguagem:     <valor>
Framework:     <valor>
Dependências:  <valor>
Domínio:       <valor>
Arquitetura:   <valor>
Arquivos:      <N> arquivos analisados
Tabelas DB:    <valor>
================================
```

---

## Relatório da Fase 2 (impresso e salvo)

```
================================
RELATÓRIO DE AUDITORIA ARQUITETURAL
================================
Projeto: <nome do repo ou pasta>
Stack:   <Linguagem + Framework>
Arquivos: <N> analisados | ~<LOC aprox> linhas de código

## Resumo
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>
Checagem de APIs deprecated: <executada — N findings | executada — nenhum encontrado>

## Findings
```

Em seguida, para cada finding, em ordem de severidade (CRITICAL → HIGH → MEDIUM → LOW) e depois por caminho de arquivo:

```
### [<SEVERIDADE>] <Nome do anti-pattern>
Arquivo: <caminho/relativo/para/arquivo>:<linha ou intervalo>
Descrição: <descrição factual em uma frase do que foi encontrado>
Impacto: <uma frase sobre a consequência>
Recomendação: <uma frase com o próximo passo concreto>
```

Fechar com:

```
================================
Total: <N> findings
================================

Fase 2 concluída. Prosseguir com a refatoração (Fase 3)? [s/n]
```

### Regras
- Todo finding **deve** ter um caminho de arquivo e um número/intervalo de linha.
- Tag de severidade em maiúsculas e entre colchetes exatamente: `[CRITICAL]`, `[HIGH]`, `[MEDIUM]`, `[LOW]`.
- Uma linha em branco entre findings.
- Não incluir nenhum outro texto entre o resumo e a lista de findings.
- Se um finding atravessa múltiplos arquivos, registrá-lo uma vez por arquivo.

---

## Bloco da Fase 3 (impresso ao final da refatoração)

```
================================
FASE 3: REFATORAÇÃO CONCLUÍDA
================================
## Nova Estrutura do Projeto
<árvore do projeto resultante — apenas src/ + arquivos de entry relevantes; omitir node_modules / __pycache__ / .venv>

## Transformações aplicadas
- <um bullet por transformação do playbook usada, citando o finding resolvido>

## Validação
  <check ou cruz> Aplicação sobe sem erros
  <check ou cruz> Todos os endpoints originalmente listados respondem
  <check ou cruz> Nenhum anti-pattern do catálogo permaneceu (ou: listar itens low remanescentes adiados)

================================
```

Usar `✓` para aprovado e `✗` para reprovado. Não declarar uma checagem como aprovada sem ter rodado de fato.
