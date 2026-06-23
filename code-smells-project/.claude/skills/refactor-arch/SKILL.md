---
name: refactor-arch
description: Analisa, audita e refatora uma codebase de backend para o padrão MVC. Detecta linguagem/framework, classifica anti-patterns por severidade, gera um relatório de auditoria e reestrutura o projeto em Models / Views (ou Routes) / Controllers preservando comportamento. Agnóstica de tecnologia — funciona para Python/Flask, Node.js/Express e stacks similares. Invocar quando o usuário digitar `/refactor-arch` ou pedir para refatorar um projeto para MVC, auditar arquitetura ou limpar code smells.
---

# refactor-arch — Skill de Refatoração Arquitetural

Executa um pipeline estrito de 3 fases sobre o diretório de trabalho atual:

1. **Fase 1 — Análise do Projeto** (somente leitura): detecta a stack, mapeia a arquitetura atual e imprime um resumo.
2. **Fase 2 — Auditoria de Arquitetura** (somente leitura): cruza o código contra o catálogo de anti-patterns, renderiza o relatório e **pausa para confirmação**.
3. **Fase 3 — Refatoração MVC** (modifica arquivos): aplica as transformações do playbook e valida boot + endpoints.

A skill é agnóstica de tecnologia. Detecte primeiro, depois conduza todas as decisões a partir dos arquivos de referência em `references/`. Nunca inclua suposições específicas sobre Flask, Express ou qualquer framework no fluxo de controle.

---

## Regras operacionais (inegociáveis)

- **Fases 1 e 2 são estritamente somente leitura.** Não editar, criar ou apagar nenhum arquivo de código durante análise ou auditoria.
- **Sempre parar após a Fase 2** e perguntar `Fase 2 concluída. Prosseguir com a refatoração (Fase 3)? [s/n]`. Não prosseguir até o usuário responder `s`.
- **Salvar o relatório de auditoria** em `reports/audit-project-{N}.md`, onde N é:
  - `1` se o diretório de trabalho termina com `code-smells-project`
  - `2` se termina com `ecommerce-api-legacy`
  - `3` se termina com `task-manager-api`
  - Caso contrário, salvar como `reports/audit.md`.
  Se a pasta `reports/` não existir, criar na raiz do diretório de trabalho.
- **Preservar comportamento.** Endpoints devem manter o mesmo método HTTP, path, formato de request e formato de response. Nenhuma rota pública pode ser renomeada ou removida sem aprovação explícita do usuário.
- **Adaptar ao estado atual.** Monolito recebe restruturação completa; projeto parcialmente organizado recebe melhorias incrementais. Não regredir estrutura válida já existente.
- **Sempre incluir detecção de APIs deprecated** na auditoria (ver catálogo).

---

## Arquivos de referência (ler sob demanda)

| Arquivo | Fase | Propósito |
|---|---|---|
| `references/project-analysis.md` | 1 | Heurísticas para detectar linguagem, framework, banco, domínio e arquitetura atual |
| `references/anti-patterns-catalog.md` | 2 | Catálogo de anti-patterns com sinais de detecção e classificação de severidade |
| `references/audit-report-template.md` | 2 | Formato exato de saída do relatório de auditoria |
| `references/mvc-guidelines.md` | 3 | Estrutura MVC alvo e responsabilidades de cada camada |
| `references/refactoring-playbook.md` | 3 | Padrões de transformação antes/depois por anti-pattern |

Não carregue todas as referências de uma vez. Carregue apenas o que a fase atual precisa.

---

## Fase 1 — Análise do Projeto (somente leitura)

1. Ler `references/project-analysis.md`.
2. Percorrer o diretório de trabalho. Detectar:
   - Linguagem (extensões de arquivos, lockfiles)
   - Framework + versão (arquivos de manifesto, imports)
   - Dependências relevantes
   - Domínio (inferir a partir de paths de rota e nomes de tabelas/models)
   - Engine e tabelas do banco
   - Arquitetura atual (Monolítica / Parcialmente organizada / MVC)
   - Quantidade de arquivos-fonte
3. Imprimir o bloco **FASE 1: ANÁLISE DO PROJETO** exatamente como definido em `references/audit-report-template.md`.
4. Continuar direto para a Fase 2 (não precisa de confirmação aqui).

---

## Fase 2 — Auditoria de Arquitetura (somente leitura)

1. Ler `references/anti-patterns-catalog.md` e `references/audit-report-template.md`.
2. Para cada arquivo-fonte, varrer todos os sinais de detecção do catálogo.
3. Registrar cada finding com:
   - Severidade (`CRITICAL` | `HIGH` | `MEDIUM` | `LOW`)
   - Nome do anti-pattern
   - Caminho do arquivo
   - Linha exata ou intervalo de linhas
   - Descrição curta
   - Impacto
   - Recomendação
4. Renderizar o **RELATÓRIO DE AUDITORIA ARQUITETURAL** seguindo o template, ordenado por severidade (CRITICAL → HIGH → MEDIUM → LOW) e depois por caminho de arquivo.
5. Salvar o relatório no caminho descrito nas regras operacionais.
6. **Imprimir exatamente:** `Fase 2 concluída. Prosseguir com a refatoração (Fase 3)? [s/n]`
7. Aguardar o usuário. Se a resposta for diferente de `s`/`sim`, parar. Caso contrário, prosseguir para a Fase 3.

Critérios mínimos de qualidade do relatório (devem valer):
- No mínimo 5 findings.
- No mínimo 1 CRITICAL ou HIGH.
- Cada finding tem um caminho real e ao menos um número de linha.
- A checagem de APIs deprecated foi executada (declarar explicitamente, mesmo sem achados).

---

## Fase 3 — Refatoração MVC (modifica arquivos)

1. Ler `references/mvc-guidelines.md` e `references/refactoring-playbook.md`.
2. Planejar a árvore alvo com base na linguagem/framework do projeto — derivar do guideline, não de um template fixo.
3. Para cada finding da Fase 2, aplicar a transformação correspondente do playbook. Se múltiplos findings têm a mesma causa raiz, agrupar em uma única transformação.
4. Adaptar à situação atual:
   - **Monolítico**: restruturação completa (config / models / views ou routes / controllers / middlewares / entry point).
   - **Parcialmente organizado**: incremental — mover apenas o que está fora do lugar; não duplicar pastas que já existem corretamente.
5. **Validar** após refatoração:
   - Subir a aplicação com o comando nativo (`python app.py`, `node src/app.js`, etc.). Confirmar que sobe sem erros.
   - Reexercitar um subconjunto representativo dos endpoints originais (usar `api.http`, tabela de rotas ou curl). Confirmar mesmos códigos HTTP e respostas equivalentes.
   - Se o boot quebrar ou qualquer endpoint regredir, corrigir antes de reportar sucesso. Não encerrar a Fase 3 com a aplicação quebrada.
6. Imprimir o bloco **FASE 3: REFATORAÇÃO CONCLUÍDA** (nova árvore + checklist de validação).

---

## Disciplina de saída

Os três cabeçalhos de fase devem ser impressos literalmente como no template. O relatório de auditoria salvo em disco deve ser byte-a-byte igual ao impresso na tela (para que o usuário possa comparar com a especificação).
