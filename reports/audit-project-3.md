================================
RELATÓRIO DE AUDITORIA ARQUITETURAL
================================
Projeto: task-manager-api
Stack:   Python 3.x + Flask 3.0.0
Arquivos: 15 analisados | ~1170 linhas de código

## Resumo
CRITICAL: 5 | HIGH: 9 | MEDIUM: 11 | LOW: 5
Checagem de APIs deprecated: executada — 3 findings (uso de `Query.get()` legado do SQLAlchemy 2.x em todas as blueprints)

## Findings

### [CRITICAL] Credenciais / Segredos Hardcoded
Arquivo: app.py:13
Descrição: `SECRET_KEY` definida como string literal `'super-secret-key-123'` no código-fonte, fora de variável de ambiente.
Impacto: o segredo vai para o histórico Git e fica visível a qualquer leitor do repositório; rotação após vazamento exige redeploy.
Recomendação: ler `SECRET_KEY` de variável de ambiente em um módulo `config/` e falhar rápido se ausente em produção.

### [CRITICAL] CORS Aberto sem allowlist
Arquivo: app.py:15
Descrição: `CORS(app)` aplicado sem `origins=[...]`, liberando qualquer origem para qualquer endpoint da API.
Impacto: habilita ataques equivalentes a CSRF a partir de qualquer site quando credenciais forem enviadas entre origens.
Recomendação: configurar `CORS(app, origins=[...])` com allowlist explícita carregada da config.

### [CRITICAL] Hash de senha fraco (MD5)
Arquivo: models/user.py:29-32
Descrição: `set_password` usa `hashlib.md5(pwd.encode()).hexdigest()` sem salt; `check_password` compara hashes MD5 diretamente.
Impacto: rainbow tables quebram MD5 instantaneamente; qualquer dump do banco expõe todas as senhas.
Recomendação: trocar para `bcrypt` / `argon2` com salt por usuário; manter o método `check_password` como única forma de comparação.

### [CRITICAL] Exposição de hash de senha em resposta da API
Arquivo: models/user.py:17-25
Descrição: `User.to_dict()` inclui o campo `password` no payload retornado, e esse dict é serializado em `/users/<id>`, `/users` (POST) e `/login`.
Impacto: clientes recebem o hash; combinado com MD5 fraco, o vazamento permite ataque offline imediato.
Recomendação: remover `password` de `to_dict()`; usar um schema de serialização (marshmallow) que nunca exporte campos sensíveis.

### [CRITICAL] Credenciais SMTP hardcoded
Arquivo: services/notification_service.py:7-10
Descrição: usuário e senha de SMTP (`taskmanager@gmail.com` / `senha123`) literais no construtor de `NotificationService`.
Impacto: credenciais de produção (caso fossem reais) vazariam no Git; mesmo placeholders viram débito de segurança.
Recomendação: ler `EMAIL_HOST`, `EMAIL_USER`, `EMAIL_PASSWORD` de variáveis de ambiente via módulo de config.

### [HIGH] Lógica de Negócio em Rotas (God Module)
Arquivo: routes/task_routes.py:1-300
Descrição: arquivo de 300 linhas concentrando validação, regras de domínio (overdue, stats, filtros), persistência e formatação de resposta dentro dos handlers.
Impacto: lógica não é reaproveitável nem testável sem subir HTTP; mudanças em regras forçam edições em vários handlers simultaneamente.
Recomendação: extrair `controllers/task_controller.py` com as operações de domínio; deixar as rotas apenas orquestrando parse → controller → response.

### [HIGH] Lógica de Negócio em Rotas (God Module)
Arquivo: routes/user_routes.py:1-211
Descrição: handlers de CRUD de usuário misturam validação manual, regex de email, hashing, cascading delete e formatação; `login` ainda emite um token fake.
Impacto: regras de autenticação e gerenciamento de usuário acopladas à camada HTTP, impossíveis de reusar em jobs/CLI.
Recomendação: criar `controllers/user_controller.py` (e `controllers/auth_controller.py`) e mover a lógica para fora dos handlers.

### [HIGH] Lógica de Negócio em Rotas (God Module)
Arquivo: routes/report_routes.py:1-224
Descrição: `summary_report` agrega contadores, calcula overdue, calcula produtividade por usuário e formata payload em uma única função; categorias compartilham o mesmo arquivo de reports indevidamente.
Impacto: lógica de relatório intransportável; mistura de domínios (reports + categories) viola coesão.
Recomendação: criar `controllers/report_controller.py` para os agregados e mover endpoints `/categories` para uma blueprint própria.

### [HIGH] Tratamento de erro silenciado (bare `except`)
Arquivo: routes/task_routes.py:62, 137, 204, 222, 236
Descrição: cinco blocos `except:` ou `except: ... rollback ... return 500` engolem qualquer exceção sem log nem distinção de causa.
Impacto: falhas reais (DB indisponível, integridade violada) são invisíveis em produção e devolvem mensagens de erro genéricas.
Recomendação: capturar exceções específicas e delegar a um error handler global do Flask que mapeia exceções para respostas JSON tipadas.

### [HIGH] Tratamento de erro silenciado (bare `except`)
Arquivo: routes/user_routes.py:87, 130, 150
Descrição: três blocos `except:` cobrindo commit/rollback de usuário sem registrar a exceção.
Impacto: bugs de integridade (email duplicado, FK quebrada) são mascarados como “Erro ao atualizar/deletar”.
Recomendação: substituir por handlers tipados e middleware central de erro.

### [HIGH] Tratamento de erro silenciado (bare `except`)
Arquivo: routes/report_routes.py:186, 207, 222
Descrição: três blocos `except:` envolvendo operações de category sem log.
Impacto: idêntico aos demais — falhas silenciosas e contrato de erro inconsistente.
Recomendação: idem — error handler global + exceções tipadas.

### [HIGH] Tratamento de erro silenciado (bare `except`)
Arquivo: utils/helpers.py:46, 48
Descrição: `parse_date` usa dois `except:` aninhados que retornam `None` em qualquer falha de parsing.
Impacto: caller perde a causa do erro; difícil distinguir “data inválida” de outras falhas inesperadas.
Recomendação: capturar `ValueError` explicitamente e propagar erro estruturado.

### [HIGH] Ausência de autenticação/autorização em rotas sensíveis
Arquivo: routes/task_routes.py:11-299
Descrição: todos os endpoints (`POST /tasks`, `PUT/DELETE /tasks/<id>`, `/tasks/stats`) são públicos — não há decorator/middleware de auth.
Impacto: qualquer cliente pode criar/alterar/deletar tasks de qualquer usuário.
Recomendação: introduzir middleware/decorator `@require_auth` e checagem de role em operações destrutivas.

### [HIGH] Ausência de autenticação/autorização em rotas sensíveis
Arquivo: routes/user_routes.py:10-183
Descrição: `GET /users`, `POST /users`, `PUT/DELETE /users/<id>` e `/users/<id>/tasks` são todos públicos, mesmo retornando PII e permitindo destruição em cascata.
Impacto: enumeração de usuários, escalonamento de privilégio (role passado pelo body), deleção arbitrária.
Recomendação: exigir auth em todos os `/users/*`, restringir mudança de `role` e `active` a admins.

### [HIGH] Ausência de autenticação/autorização em rotas sensíveis
Arquivo: routes/report_routes.py:12-223
Descrição: `/reports/summary`, `/reports/user/<id>` e CRUD de `/categories` expostos sem auth.
Impacto: vazamento de métricas internas e edição livre do catálogo de categorias.
Recomendação: aplicar o mesmo middleware de auth e adicionar guarda de role para os endpoints de categories.

### [HIGH] Autenticação insegura (token fake em `/login`)
Arquivo: routes/user_routes.py:207-211
Descrição: endpoint retorna `'fake-jwt-token-' + str(user.id)` como token de sessão.
Impacto: não há verificação criptográfica — qualquer cliente pode forjar o token concatenando um id; toda a “autenticação” da API é teatro.
Recomendação: emitir JWT real assinado (PyJWT/authlib) com claims e expiração; validar via decorator nas rotas protegidas.

### [HIGH] Acoplamento forte — sem injeção de dependência
Arquivo: routes/task_routes.py:1-9 (e equivalentes em routes/user_routes.py:1-7, routes/report_routes.py:1-8)
Descrição: cada blueprint importa `db`, `Task`, `User`, `Category` diretamente no nível do módulo e os usa estaticamente.
Impacto: impossível substituir o repositório por fakes em testes; qualquer mudança no acesso a dados se espalha por todas as rotas.
Recomendação: extrair uma camada de repository por entidade e injetá-la nos controllers; conectar uma única vez no entry point.

### [MEDIUM] API SQLAlchemy deprecated (`Query.get()`)
Arquivo: routes/task_routes.py:67, 158, 188, 195, 227
Descrição: uso de `Task.query.get(...)`, `User.query.get(...)` e `Category.query.get(...)` — padrão legado removido do estilo idiomático no SQLAlchemy 2.x.
Impacto: emite `LegacyAPIWarning`; será removido em versões futuras; quebra com auto-detecção de breaking changes.
Recomendação: substituir por `db.session.get(Model, id)`.

### [MEDIUM] API SQLAlchemy deprecated (`Query.get()`)
Arquivo: routes/user_routes.py:29, 94, 135, 156
Descrição: idem — `User.query.get(user_id)` em quatro handlers.
Impacto: idem.
Recomendação: idem — usar `db.session.get(User, user_id)`.

### [MEDIUM] API SQLAlchemy deprecated (`Query.get()`)
Arquivo: routes/report_routes.py:105, 192, 213
Descrição: idem para `User.query.get(...)` e `Category.query.get(...)` nas rotas de relatório e categoria.
Impacto: idem.
Recomendação: idem — migrar para `db.session.get(Model, id)`.

### [MEDIUM] Validação no handler em vez de schema
Arquivo: routes/task_routes.py:96-114, 167-184
Descrição: limites de título, lista de status, faixa de prioridade e formato de data validados manualmente com `if` espalhados em cada handler.
Impacto: regras divergem entre POST e PUT; mensagens de erro inconsistentes; sem reaproveitamento.
Recomendação: definir `TaskSchema` em marshmallow (já está no requirements) e validar uma vez na entrada do handler.

### [MEDIUM] Validação no handler em vez de schema
Arquivo: routes/user_routes.py:54-72, 102-122
Descrição: regex de email, comprimento de senha e enum de role validados manualmente; lógica duplicada entre create e update.
Impacto: divergência entre rotas, regex copiada em dois lugares (linhas 61 e 106).
Recomendação: extrair `UserSchema` (create/update) com marshmallow.

### [MEDIUM] Duplicação de código — cálculo de “overdue”
Arquivo: routes/task_routes.py:30-39, 71-80, 282-287
Descrição: o mesmo bloco `if t.due_date < utcnow() and status not in ('done','cancelled')` aparece três vezes só neste arquivo.
Impacto: divergência de regra é inevitável; já há um `Task.is_overdue()` no model que está sendo ignorado.
Recomendação: chamar `task.is_overdue()` ou mover a regra para um service/property única.

### [MEDIUM] Duplicação de código — cálculo de “overdue”
Arquivo: routes/user_routes.py:171-180
Descrição: replica o mesmo bloco em `/users/<id>/tasks` em vez de chamar o método já existente no modelo.
Impacto: idem.
Recomendação: reusar `task.is_overdue()`.

### [MEDIUM] Duplicação de código — cálculo de “overdue”
Arquivo: routes/report_routes.py:33-43, 132-135
Descrição: o mesmo cálculo se repete no `summary_report` e no `user_report`.
Impacto: idem.
Recomendação: encapsular em service/repository (`TaskRepository.list_overdue(...)`).

### [MEDIUM] Query N+1 ao listar tasks
Arquivo: routes/task_routes.py:41-57
Descrição: `get_tasks` faz um `Task.query.all()` e dentro do loop chama `User.query.get(t.user_id)` e `Category.query.get(t.category_id)` para cada task.
Impacto: latência cresce linearmente com o número de tasks; sob volume real, vira o gargalo dominante.
Recomendação: usar `joinedload(Task.user, Task.category)` ou um `db.session.execute(select(...).options(...))`.

### [MEDIUM] Query N+1 ao listar usuários
Arquivo: routes/user_routes.py:22, 35-38
Descrição: `len(u.tasks)` no loop dispara lazy-load por usuário; `/users/<id>` também itera `Task.query.filter_by(...)` cuja saída chama `to_dict()` por linha.
Impacto: idem — round-trips por linha.
Recomendação: agregar via SQL (`func.count`) e usar eager loading; serializar com schema.

### [MEDIUM] Query N+1 no relatório por usuário
Arquivo: routes/report_routes.py:53-68
Descrição: para cada usuário, `summary_report` executa `Task.query.filter_by(user_id=u.id).all()` e conta `done` em Python.
Impacto: o relatório-resumo, que deveria ser uma agregação, vira N consultas + processamento em memória.
Recomendação: usar `GROUP BY user_id, status` em uma única query SQL.

### [MEDIUM] Logging via `print()`
Arquivo: routes/task_routes.py:149, 153, 219, 234
Descrição: eventos de criação/atualização/deleção e mensagens de erro emitidos via `print`.
Impacto: sem níveis, sem correlação por request, sem encaminhamento estruturado; some no `stdout` em produção.
Recomendação: usar `logging.getLogger(__name__)` com handler configurado no entry point.

### [MEDIUM] Logging via `print()`
Arquivo: routes/user_routes.py:83, 89, 147
Descrição: criação, erro e deleção de usuários logados via `print`.
Impacto: idem.
Recomendação: idem — logger nomeado.

### [MEDIUM] Logging via `print()`
Arquivo: services/notification_service.py:21, 24
Descrição: envio de email e falha logados via `print`.
Impacto: idem — sem correlação nem nível.
Recomendação: idem — `logger.info` / `logger.exception`.

### [LOW] Imports não utilizados
Arquivo: app.py:7
Descrição: `os, sys, json` importados e nunca usados.
Impacto: ruído de leitura; pistas falsas sobre dependências.
Recomendação: remover.

### [LOW] Imports não utilizados
Arquivo: utils/helpers.py:3-7
Descrição: `os`, `json`, `sys`, `math`, `hashlib` importados sem uso.
Impacto: idem.
Recomendação: remover.

### [LOW] Código morto — `NotificationService` nunca instanciado
Arquivo: services/notification_service.py:1-49
Descrição: classe completa sem nenhum import em outros arquivos do projeto.
Impacto: lê como funcionalidade existente quando não está; segredos hardcoded sem propósito.
Recomendação: ou integrar (instanciar via config + chamar nos pontos certos) ou remover; o histórico Git preserva.

### [LOW] Código morto em utils/helpers.py
Arquivo: utils/helpers.py:19-116
Descrição: `validate_email`, `sanitize_string`, `generate_id`, `log_action`, `parse_date`, `is_valid_color`, `process_task_data` e as constantes `VALID_STATUSES/VALID_ROLES/MAX_TITLE_LENGTH/...` não têm referência fora do próprio arquivo; apenas `format_date`/`calculate_percentage` são importadas em `report_routes.py:7`, e mesmo essas não são chamadas no corpo do arquivo.
Impacto: arquivo aparenta ser utilitário compartilhado mas é morto; convida a reimplementações divergentes.
Recomendação: remover o que não é usado; manter apenas helpers efetivamente consumidos pelos controllers.

### [LOW] Magic strings — valores de status repetidos
Arquivo: routes/task_routes.py:110, 177, 286 (também em models/task.py:39)
Descrição: lista `['pending', 'in_progress', 'done', 'cancelled']` redigitada em 4 lugares.
Impacto: divergência inevitável; já existe `VALID_STATUSES` em `utils/helpers.py` que ninguém usa.
Recomendação: definir um enum (`enum.Enum`) ou constantes em `constants.py` e referenciar de um único ponto.

================================
Total: 30 findings
================================

Fase 2 concluída. Prosseguir com a refatoração (Fase 3)? [s/n]
