# Desafio de Skills — Refatoração Arquitetural Automatizada

Skill de refatoração arquitetural criada com **Claude Code Custom Skills**. Analisa qualquer projeto de backend, detecta anti-patterns, gera um relatório de auditoria estruturado e reestrutura o código para o padrão MVC — de forma agnóstica de tecnologia.

---

## Análise Manual

### Projeto 1 — `code-smells-project` (Python/Flask — API de E-commerce)

**Estrutura original:** 4 arquivos (`app.py`, `controllers.py`, `models.py`, `database.py`) sem separação de camadas.

| Severidade | Problema | Arquivo | Justificativa |
|---|---|---|---|
| **CRITICAL** | Credenciais hardcoded | `app.py:7` | `SECRET_KEY = "minha-chave-super-secreta-123"` vai para o histórico Git e compromete assinatura de sessões. |
| **CRITICAL** | Segredo exposto via endpoint público | `controllers.py:285-290` | `GET /health` devolve `secret_key` e `db_path` no corpo JSON, sem autenticação. |
| **CRITICAL** | SQL Injection generalizada | `models.py` (20+ pontos) | 100% das queries monta SQL por concatenação de string com input do usuário, permitindo bypass de login via `' OR 1=1 --`. |
| **CRITICAL** | Endpoint de SQL arbitrário sem auth | `app.py:59-78` | `POST /admin/query` aceita SQL bruto e executa direto no banco — equivale a RCE sobre o banco. |
| **HIGH** | God Module | `models.py:1-315` | 315 linhas misturando queries, lógica de negócio, cálculo de descontos e formatação de 4 domínios distintos. |
| **HIGH** | Autenticação ausente em endpoints sensíveis | `app.py:11-30` | Nenhuma rota exige auth; `GET /usuarios` retorna o campo `senha` em claro para qualquer cliente. |
| **MEDIUM** | Queries N+1 | `models.py:171-233` | Para cada pedido, faz SELECT em itens e depois SELECT por produto — até `1 + N + N×M` round-trips. |
| **MEDIUM** | Validação de input ausente | `controllers.py:146-255` | Nenhum handler valida tipo, formato ou presença dos campos; quantidade negativa entra sem erro. |
| **LOW** | Magic numbers e listas hardcoded | `models.py:257-262` | Limiares de desconto (`10000/5000/1000`) e taxas (`0.1/0.05/0.02`) espalhadas como literais. |
| **LOW** | Nomenclatura ruim | `controllers.py:14, 64, 98` | Parâmetro `id` sombreia o builtin Python; `dados` genérico em todos os handlers. |

---

### Projeto 2 — `ecommerce-api-legacy` (Node.js/Express — LMS API)

**Estrutura original:** 3 arquivos (`src/app.js`, `src/AppManager.js`, `src/utils.js`) num monolito.

| Severidade | Problema | Arquivo | Justificativa |
|---|---|---|---|
| **CRITICAL** | God Class | `src/AppManager.js:1-142` | Uma única classe concentra DB, schema, seeds, roteamento, checkout, pagamento, relatório e auditoria. |
| **CRITICAL** | Credenciais hardcoded | `src/utils.js:1-7` | `paymentGatewayKey = "pk_live_1234567890abcdef"` e senha SMTP literais — entram no histórico Git. |
| **CRITICAL** | Hash de senha fraco | `src/utils.js:17-23` | `badCrypto` faz loop de `base64` sem salt — reversível instantaneamente por rainbow table. |
| **HIGH** | Lógica de negócio no handler (checkout) | `src/AppManager.js:28-78` | Validação, busca, criação de usuário, pagamento, matrícula e auditoria dentro de uma cascata de callbacks. |
| **HIGH** | Autenticação ausente em endpoint admin | `src/AppManager.js:80` | `GET /api/admin/financial-report` expõe receita e PII de alunos sem nenhum middleware de auth. |
| **HIGH** | Erro silenciado (audit log) | `src/AppManager.js:57` | `err` ignorado no callback do INSERT audit — falha de auditoria vira `200 Sucesso`. |
| **MEDIUM** | Query N+1 no relatório | `src/AppManager.js:89-127` | Para cada curso: SELECT enrollments; para cada enrollment: SELECT user + SELECT payment. |
| **MEDIUM** | Logging com vazamento de PII | `src/AppManager.js:45` | `console.log` imprime número de cartão de crédito **e** chave do gateway a cada checkout. |
| **LOW** | Magic string no processamento de pagamento | `src/AppManager.js:46` | `cc.startsWith("4") ? "PAID" : "DENIED"` — regra de negócio embutida em literal. |
| **LOW** | Código morto | `src/utils.js:10` | `totalRevenue = 0` declarado, exportado, mas nunca lido nem mutado. |

---

### Projeto 3 — `task-manager-api` (Python/Flask — API de Task Manager)

**Estrutura original:** parcialmente organizada — `models/`, `routes/`, `services/`, `utils/` existem, mas com fortes violações de responsabilidade.

| Severidade | Problema | Arquivo | Justificativa |
|---|---|---|---|
| **CRITICAL** | Hash de senha fraco (MD5) | `models/user.py:29-32` | `hashlib.md5(pwd.encode())` sem salt — rainbow tables quebram instantaneamente. |
| **CRITICAL** | Credenciais SMTP hardcoded | `services/notification_service.py:7-10` | `senha123` literal no construtor — viram débito de segurança mesmo sendo placeholder. |
| **HIGH** | Lógica de negócio em rotas (God Module) | `routes/task_routes.py:1-300` | 300 linhas com validação, regras de domínio, filtros, persistência e formatação dentro dos handlers. |
| **HIGH** | Autenticação fake via token forjável | `routes/user_routes.py:207-211` | Retorna `'fake-jwt-token-' + str(user.id)` — qualquer cliente forja token concatenando um id. |
| **HIGH** | Bare `except` silenciando erros | `routes/task_routes.py:62, 137, 204, 222, 236` | 5 blocos `except:` sem log nem causa — falhas reais ficam invisíveis em produção. |
| **HIGH** | Autenticação ausente em todas as rotas | `routes/task_routes.py`, `routes/user_routes.py` | Todos os endpoints públicos — qualquer cliente cria, altera ou deleta tasks/usuários de qualquer pessoa. |
| **MEDIUM** | API SQLAlchemy deprecated (`Query.get()`) | `routes/task_routes.py`, `routes/user_routes.py`, `routes/report_routes.py` | `Model.query.get(id)` legado do SQLAlchemy 2.x — emite `LegacyAPIWarning`; será removido. |
| **MEDIUM** | Duplicação de cálculo "overdue" | `routes/task_routes.py:30-39, 71-80, 282-287` | Mesmo bloco de 6 linhas repetido 5 vezes; `Task.is_overdue()` já existe no model e é ignorado. |
| **LOW** | Imports não utilizados | `app.py:7`, `utils/helpers.py:3-7` | `os`, `sys`, `json`, `math`, `hashlib` importados sem uso — ruído de leitura. |
| **LOW** | Código morto em helpers | `utils/helpers.py:19-116` | 8 funções (`validate_email`, `sanitize_string`, etc.) declaradas mas sem referências no projeto. |

---

## Construção da Skill

### Estrutura dos arquivos

```
.claude/skills/refactor-arch/
├── SKILL.md                          ← Arquivo de controle (fases, regras, disciplina de saída)
└── references/
    ├── project-analysis.md           ← Heurísticas de detecção de stack e arquitetura
    ├── anti-patterns-catalog.md      ← 18 anti-patterns com sinais e severidade
    ├── audit-report-template.md      ← Template exato do relatório (Fase 2)
    ├── mvc-guidelines.md             ← Regras MVC alvo por camada
    └── refactoring-playbook.md       ← 12 transformações antes/depois por anti-pattern
```

**Decisão de design:** separar o `SKILL.md` (orquestração) dos arquivos de referência (conhecimento de domínio) para que o agente carregue apenas o que a fase atual precisa — isso reduz o contexto consumido e evita "poluição" de instruções entre fases.

### Anti-patterns no catálogo (18 no total)

| Severidade | Anti-patterns |
|---|---|
| CRITICAL (5) | God Class/Module · Credenciais Hardcoded · SQL Injection · Hash de Senha Fraco · CORS Aberto |
| HIGH (5) | Lógica de Negócio em Rotas · Acoplamento Forte (sem DI) · Estado Global Mutável · Erro Silenciado · Auth Ausente |
| MEDIUM (5) | Query N+1 · Validação de Input Ausente · Duplicação de Código · APIs Deprecated · Logging Inadequado |
| LOW (3) | Magic Numbers · Nomenclatura Ruim · Código Morto |

O catálogo inclui obrigatoriamente **detecção de APIs deprecated** (Python/Flask, SQLAlchemy 2.x, Node.js, Express, MongoDB) com lista de substituições modernas.

### Como a skill é agnóstica de tecnologia

- **Fase 1** usa heurísticas baseadas em extensão de arquivo, lockfiles e padrões de manifesto — não assume Python nem Node.
- **Fase 2** usa sinais de detecção que funcionam em qualquer linguagem (ex.: `"SELECT ... WHERE id = " + variavel` é SQLi em qualquer stack).
- **Fase 3** deriva a estrutura MVC alvo da linguagem detectada na Fase 1, usando os templates do `mvc-guidelines.md` — não há estrutura fixa hard-coded no `SKILL.md`.
- A regra "monolito → restruturação completa; parcialmente organizado → incremental" é expressa como critério, não como lista de passos para um projeto específico.

### Desafios e decisões

| Desafio | Solução |
|---|---|
| A confirmação da Fase 2 é obrigatória antes de qualquer edição | Regra explícita no `SKILL.md`: `Sempre parar após a Fase 2` + instrução de aguardar `s` do usuário |
| Projeto 3 já tem `models/`, `routes/`, `services/` — não deve regridir | Regra "Adaptar ao estado atual" instrui o agente a fazer incrementos, não reescritas |
| Garantir que o relatório salvo seja igual ao impresso | Disciplina de saída: "relatório salvo em disco deve ser byte-a-byte igual ao impresso na tela" |
| Detecção de APIs deprecated varia muito por stack | Entrada dedicada no catálogo com lista por framework; verificação declarada mesmo quando sem achados |

---

## Resultados

### Resumo dos relatórios de auditoria

| Projeto | Stack | Arquivos | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|---|---|
| code-smells-project | Python/Flask 3.1.1 | 4 (~780 linhas) | 8 | 7 | 5 | 3 | **23** |
| ecommerce-api-legacy | Node.js/Express 4.18 | 3 (~182 linhas) | 4 | 8 | 4 | 3 | **19** |
| task-manager-api | Python/Flask 3.0.0 | 15 (~1170 linhas) | 5 | 9 | 11 | 5 | **30** |

### Comparação antes/depois da estrutura

#### Projeto 1 — code-smells-project

**Antes:**
```
code-smells-project/
├── app.py          ← config, rotas, endpoints admin sem auth
├── controllers.py  ← handlers com lógica de negócio + N+1 + prints
├── models.py       ← god module com SQLi, senhas em claro, 315 linhas
└── database.py     ← singleton global com check_same_thread=False
```

**Depois (alvo MVC):**
```
code-smells-project/
├── config/settings.py           ← variáveis de ambiente
├── models/
│   ├── produto_model.py
│   ├── usuario_model.py
│   └── pedido_model.py
├── routes/
│   ├── produto_routes.py
│   ├── usuario_routes.py
│   └── pedido_routes.py
├── controllers/
│   ├── produto_controller.py
│   ├── usuario_controller.py
│   └── pedido_controller.py
├── middlewares/error_handler.py
└── app.py                       ← composition root
```

---

#### Projeto 2 — ecommerce-api-legacy

**Antes:**
```
ecommerce-api-legacy/src/
├── app.js          ← apenas sobe o servidor
├── AppManager.js   ← god class com DB, rotas, checkout, pagamento, relatório
└── utils.js        ← secrets hardcoded, badCrypto, estado global
```

**Depois (alvo MVC):**
```
ecommerce-api-legacy/src/
├── config/index.js              ← process.env, falha rápido se ausente
├── models/
│   ├── User.js
│   ├── Course.js
│   ├── Enrollment.js
│   └── Payment.js
├── routes/
│   ├── checkout.routes.js
│   ├── report.routes.js
│   └── users.routes.js
├── controllers/
│   ├── checkout.controller.js
│   ├── report.controller.js
│   └── users.controller.js
├── middlewares/errorHandler.js
├── app.js                       ← composition root (exporta `app`)
└── server.js                    ← importa app, chama listen()
```

---

#### Projeto 3 — task-manager-api

**Antes:**
```
task-manager-api/
├── app.py                        ← secrets hardcoded, imports não usados
├── models/{user,task,category}.py ← MD5 sem salt, to_dict() expõe senha
├── routes/{task,user,report}_routes.py ← god modules de 200-300 linhas
├── services/notification_service.py   ← SMTP hardcoded, nunca instanciada
└── utils/helpers.py                   ← 100 linhas de código morto
```

**Depois (alvo — incremental, mantendo camadas válidas):**
```
task-manager-api/
├── config/settings.py            ← carrega SECRET_KEY, SMTP via os.environ
├── models/{user,task,category}.py ← bcrypt, to_dict() sem campo senha
├── routes/{task,user,report}_routes.py ← apenas parse → controller → resposta
├── controllers/
│   ├── task_controller.py
│   ├── user_controller.py
│   ├── report_controller.py
│   └── category_controller.py
├── middlewares/error_handler.py  ← handler central substituindo bare except
├── services/notification_service.py   ← SMTP via os.environ, testável
└── app.py                        ← composition root com factory create_app()
```

---

### Checklist de validação

> **Status:** Fases 1, 2 e 3 concluídas nos 3 projetos.

#### Projeto 1 — code-smells-project

**Fase 1 — Análise**
- [x] Linguagem detectada corretamente (Python)
- [x] Framework detectado corretamente (Flask 3.1.1)
- [x] Domínio descrito corretamente (E-commerce API: produtos, pedidos, usuários)
- [x] Número de arquivos analisados (4) condiz com a realidade

**Fase 2 — Auditoria**
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (23 encontrados)
- [x] Detecção de APIs deprecated incluída (nenhum encontrado — declarado explicitamente)
- [x] Skill pausou e pediu confirmação antes da Fase 3

**Fase 3 — Refatoração**
- [x] Estrutura de diretórios segue padrão MVC (`config/`, `models/`, `routes/`, `controllers/`, `middlewares/`)
- [x] Configuração extraída para `config/settings.py` — `SECRET_KEY`, `DB_PATH`, `CORS_ORIGINS` via `os.environ`
- [x] Models criados por domínio: `produto_model.py`, `usuario_model.py`, `pedido_model.py` — queries 100% parametrizadas
- [x] Routes separadas por Blueprint: `produto_routes.py`, `usuario_routes.py`, `pedido_routes.py`
- [x] Controllers concentram validação e orquestração: `produto_controller.py`, `usuario_controller.py`, `pedido_controller.py`
- [x] Error handling centralizado em `middlewares/error_handler.py` (handlers para HttpError, ValueError, Exception)
- [x] Entry point `app.py` com factory `create_app()` — < 60 linhas, sem lógica de negócio
- [x] Aplicação inicia sem erros (`INFO database Banco inicializado com dados de seed.`)
- [x] Endpoints originais respondem corretamente (testados: `GET /`, `/health`, `/produtos`, `/produtos/busca`, `/produtos/1`, `POST /login`, `GET /usuarios`, `POST /pedidos`, `GET /pedidos/usuario/2`, `PUT /pedidos/1/status`, `GET /relatorios/vendas`)

**Correções de segurança aplicadas:**
- Senhas hasheadas com bcrypt (coluna `password_hash`)
- Endpoints `/admin/reset-db` e `/admin/query` removidos
- `/health` não expõe mais `secret_key`, `db_path` ou `debug`
- CORS restrito a `CORS_ORIGINS` da config
- Debug desativado por padrão (`DEBUG=false` em `.env.example`)
- N+1 nas queries de pedidos resolvido com JOIN único
- `print()` substituído por `logging.getLogger(__name__)`

---

#### Projeto 2 — ecommerce-api-legacy

**Fase 1 — Análise**
- [x] Linguagem detectada corretamente (Node.js)
- [x] Framework detectado corretamente (Express 4.18)
- [x] Domínio descrito corretamente (LMS API: cursos, matrículas, checkout, pagamento)
- [x] Número de arquivos analisados (3) condiz com a realidade

**Fase 2 — Auditoria**
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (19 encontrados)
- [x] Detecção de APIs deprecated incluída (nenhum encontrado — declarado explicitamente)
- [x] Skill pausou e pediu confirmação antes da Fase 3

**Fase 3 — Refatoração**
- [x] Estrutura de diretórios segue padrão MVC (`config/`, `models/`, `routes/`, `controllers/`, `middlewares/`, `database/`)
- [x] Configuração extraída para `src/config/index.js` — `PAYMENT_GATEWAY_KEY`, `SMTP_*` via `process.env`
- [x] Models por entidade: `User.js`, `Course.js`, `Enrollment.js`, `Payment.js`, `AuditLog.js`
- [x] Routes separadas: `checkout.routes.js`, `report.routes.js`, `users.routes.js`
- [x] Controllers orquestram regras: `checkout.controller.js`, `report.controller.js`, `users.controller.js`
- [x] Error handling centralizado em `middlewares/errorHandler.js` com `HttpError` e middleware Express
- [x] Entry point separado: `app.js` (factory `createApp()`) + `server.js` (chama `listen()`)
- [x] Aplicação inicia sem erros (`LMS API running on port 3000`)
- [x] Endpoints originais respondem corretamente: `POST /api/checkout` (sucesso + recusado), `GET /api/admin/financial-report`, `DELETE /api/users/:id` (com 404 para não encontrado)

**Correções de segurança aplicadas:**
- `badCrypto` removido → bcryptjs com salt
- Secrets (`paymentGatewayKey`, `dbPass`, `smtpUser`) movidos para `process.env`
- `globalCache` e `totalRevenue` (estado global mutável) removidos
- Erro silenciado no audit log → propagado via `next(err)`
- DELETE retorna 404 quando usuário não existe (antes retornava 200 sempre)
- Logging de PII removido (cartão de crédito e chave do gateway não são mais logados)
- N+1 no relatório financeiro resolvido com JOIN único

---

#### Projeto 3 — task-manager-api

**Fase 1 — Análise**
- [x] Linguagem detectada corretamente (Python)
- [x] Framework detectado corretamente (Flask 3.0.0)
- [x] Domínio descrito corretamente (Task Manager API)
- [x] Número de arquivos analisados (15) condiz com a realidade

**Fase 2 — Auditoria**
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (30 encontrados)
- [x] Detecção de APIs deprecated incluída (3 findings — `Query.get()` legado SQLAlchemy 2.x)
- [x] Skill pausou e pediu confirmação antes da Fase 3

**Fase 3 — Refatoração**
- [x] Estrutura de diretórios segue padrão MVC (`config/`, `models/`, `routes/`, `controllers/`, `middlewares/`, `services/`)
- [x] Configuração extraída para `config/settings.py` — `SECRET_KEY`, `DATABASE_URL`, `CORS_ORIGINS`, `SMTP_*` via `os.environ`
- [x] Models por domínio com bcrypt: `user.py` (senha não exposta em `to_dict()`), `task.py`, `category.py`
- [x] Routes reescritas como thin handlers: `task_routes.py`, `user_routes.py`, `report_routes.py`, `category_routes.py`
- [x] Controllers concentram lógica: `task_controller.py`, `user_controller.py`, `report_controller.py`, `category_controller.py`
- [x] Error handling centralizado em `middlewares/error_handler.py` — `HttpError` + handler para `Exception`
- [x] Entry point `app.py` com factory `create_app()` — CORS restrito, sem lógica de negócio
- [x] Aplicação inicia sem erros (`python app.py` / `python -c "from app import create_app; create_app()"`)
- [x] Endpoints respondem corretamente: `GET /health` (200), `GET /tasks` (200), `POST /users` (201 sem campo `password`), `POST /login` (200, token `secrets.token_hex(32)`), `GET /tasks/stats` (200), `GET /reports/summary` (200), `GET /tasks/999` (404), `POST /users` inválido (400)

**Correções de segurança aplicadas:**
- MD5 sem salt substituído por bcrypt 4.x
- Campo `password` removido do `to_dict()` do modelo User
- Token fake (`fake-jwt-token-<id>`) substituído por `secrets.token_hex(32)`
- Credenciais SMTP movidas para `os.environ` (`SMTP_USER`, `SMTP_PASS`)
- 5 blocos `bare except:` substituídos por erros propagados via `HttpError`
- `Query.get()` deprecated substituído por `db.session.get()`
- `overdue` duplicado 5x → usa `task.is_overdue()` já disponível no model
- N+1 no `summary_report` (loop de users/tasks) resolvido com `joinedload(User.tasks)`
- N+1 em `get_tasks` resolvido com `joinedload(Task.user, Task.category)`
- `print()` substituído por `logging.getLogger(__name__)`
- Código morto em `utils/helpers.py` removido (8 funções sem referências)

---

### Observações sobre a skill em stacks diferentes

- **Python/Flask monolítico (Projeto 1):** a skill identificou a natureza "flat" dos 4 arquivos e planejou reestruturação completa para MVC. O catálogo de SQLi foi especialmente eficaz aqui, encontrando 20+ pontos de injeção.
- **Node.js/Express (Projeto 2):** a skill adaptou a estrutura alvo para `app.js` + `server.js` (convenção Node), detectou `badCrypto` via sinal de "hash fraco" e localizou o padrão N+1 de callbacks aninhados.
- **Python/Flask parcialmente organizado (Projeto 3):** a skill respeitou `models/`, `routes/` e `services/` já existentes, propondo incremento (adicionar `controllers/`, `config/`, `middlewares/`) sem regridir estrutura válida. A detecção de APIs deprecated SQLAlchemy foi o diferencial — encontrou 10 chamadas `Query.get()` legadas distribuídas por 3 blueprints.

---

## Como Executar

### Pré-requisitos

- **Claude Code** instalado e configurado (`claude --version`)
- Conta Anthropic com acesso ao Claude Code
- Para os projetos Python: Python 3.10+ e `pip`
- Para o projeto Node.js: Node.js 18+ e `npm`

### Executar a skill em cada projeto

```bash
# Projeto 1 — Python/Flask (E-commerce)
cd code-smells-project
claude "/refactor-arch"
# Aguardar a Fase 1 e Fase 2; revisar o relatório; digitar "s" para confirmar a Fase 3

# Projeto 2 — Node.js/Express (LMS)
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3 — Python/Flask (Task Manager)
cd ../task-manager-api
claude "/refactor-arch"
```

Os relatórios de auditoria são salvos automaticamente pela skill em:
- `reports/audit-project-1.md`
- `reports/audit-project-2.md`
- `reports/audit-project-3.md`

### Validar que a refatoração funcionou

**Projeto 1 (Python/Flask):**
```bash
cd code-smells-project
pip install -r requirements.txt
python app.py
# Em outro terminal:
curl http://localhost:5000/produtos
curl http://localhost:5000/health
```

**Projeto 2 (Node.js/Express):**
```bash
cd ecommerce-api-legacy
npm install
node src/app.js   # ou: node src/server.js após refatoração
# Em outro terminal:
curl http://localhost:3000/api/admin/financial-report
# Consultar api.http para os demais endpoints
```

**Projeto 3 (Python/Flask):**
```bash
cd task-manager-api
pip install -r requirements.txt
python app.py
# Em outro terminal:
curl http://localhost:5000/tasks
curl http://localhost:5000/users
curl http://localhost:5000/reports/summary
```

### Estrutura da skill (para referência ou customização)

```
.claude/skills/refactor-arch/
├── SKILL.md                          # Orquestração das 3 fases e regras de comportamento
└── references/
    ├── project-analysis.md           # Heurísticas de detecção de stack
    ├── anti-patterns-catalog.md      # 18 anti-patterns com sinais e severidade
    ├── audit-report-template.md      # Formato exato do relatório
    ├── mvc-guidelines.md             # Arquitetura MVC alvo por camada
    └── refactoring-playbook.md       # 12 transformações antes/depois
```

A skill está copiada nos 3 projetos:
- `code-smells-project/.claude/skills/refactor-arch/`
- `ecommerce-api-legacy/.claude/skills/refactor-arch/`
- `task-manager-api/.claude/skills/refactor-arch/`
