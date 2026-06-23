================================
RELATÓRIO DE AUDITORIA ARQUITETURAL
================================
Projeto: code-smells-project
Stack:   Python + Flask 3.1.1
Arquivos: 4 analisados | ~780 linhas de código

## Resumo
CRITICAL: 8 | HIGH: 7 | MEDIUM: 5 | LOW: 3
Checagem de APIs deprecated: executada — nenhum encontrado (as APIs do Flask 3.x em uso ainda são suportadas; nenhum símbolo deprecated identificado nas dependências atuais)

## Findings

### [CRITICAL] Credenciais Hardcoded
Arquivo: app.py:7
Descrição: SECRET_KEY definida como string literal "minha-chave-super-secreta-123" diretamente no código-fonte.
Impacto: Segredo versionado no Git fica exposto a qualquer pessoa com acesso ao repositório; rotação após vazamento exige redeploy.
Recomendação: Carregar de variável de ambiente em um módulo config/settings.py; falhar rápido em produção se ausente.

### [CRITICAL] Segredo Exposto via Endpoint Público
Arquivo: controllers.py:285-290
Descrição: O endpoint GET /health retorna no corpo JSON os campos `secret_key`, `db_path` e `debug`, expondo o SECRET_KEY do servidor.
Impacto: Qualquer cliente HTTP, sem autenticação, obtém o SECRET_KEY apenas chamando o health-check; comprometimento total da assinatura de sessões/tokens.
Recomendação: Remover campos sensíveis do payload de /health; manter apenas status e contagens.

### [CRITICAL] SQL Injection generalizada na camada de dados
Arquivo: models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-151, 155-161, 163-166, 174, 188, 192, 220, 224, 280, 289-297
Descrição: Toda função do módulo models.py monta SQL por concatenação de strings com inputs do usuário — get_produto_por_id, criar_produto, atualizar_produto, deletar_produto, get_usuario_por_id, login_usuario, criar_usuario, criar_pedido, get_pedidos_usuario, atualizar_status_pedido e buscar_produtos.
Impacto: Toda a superfície de dados é vulnerável a SQLi. login_usuario (linha 109-111) permite bypass trivial de autenticação via payload `' OR 1=1 --`; buscar_produtos permite injetar UNION SELECT.
Recomendação: Migrar 100% das queries para placeholders parametrizados — `cursor.execute("SELECT ... WHERE id = ?", (id,))`.

### [CRITICAL] Endpoint de Execução de SQL Arbitrário
Arquivo: app.py:59-78
Descrição: A rota POST /admin/query aceita SQL bruto no body e executa diretamente no banco, sem autenticação nem allowlist.
Impacto: Equivalente a RCE sobre o banco — qualquer cliente pode ler, alterar ou dropar qualquer tabela em uma única requisição.
Recomendação: Remover o endpoint. Se administração via API for necessária, expor operações específicas (não SQL bruto) atrás de autenticação forte.

### [CRITICAL] Endpoint Admin Destrutivo sem Autenticação
Arquivo: app.py:47-57
Descrição: A rota POST /admin/reset-db apaga todas as tabelas (itens_pedido, pedidos, produtos, usuarios) sem autenticação ou confirmação.
Impacto: Qualquer cliente da rede pode zerar o banco de produção em uma única requisição.
Recomendação: Exigir autenticação de admin + confirmação explícita; preferencialmente, mover para um script CLI fora da API HTTP.

### [CRITICAL] Armazenamento de Senhas em Texto Puro
Arquivo: database.py:31, 76-79; models.py:127-129
Descrição: A coluna `usuarios.senha` é declarada como TEXT e recebe senhas em claro; o seed insere "admin123", "123456", "senha123" sem hashing.
Impacto: Qualquer dump (legítimo ou hostil) do banco vaza todas as credenciais; reuso de senhas em outros serviços compromete os usuários.
Recomendação: Renomear coluna para `password_hash`; gerar hash com bcrypt/argon2 ao criar; comparar com bcrypt.checkpw no login.

### [CRITICAL] Bypass de Autenticação via SQLi no Login
Arquivo: models.py:105-120
Descrição: login_usuario monta `WHERE email = '<email>' AND senha = '<senha>'` por concatenação e compara senhas em claro.
Impacto: Bypass trivial de autenticação combinando SQLi (`' OR '1'='1`) com ausência de hash; um único POST a /login retorna a sessão de qualquer usuário.
Recomendação: Buscar usuário com query parametrizada (apenas por email); validar senha via hmac/bcrypt sobre o hash armazenado.

### [CRITICAL] Modo Debug Habilitado no Caminho de Produção
Arquivo: app.py:8, app.py:88
Descrição: `app.config["DEBUG"] = True` e `app.run(host="0.0.0.0", port=5000, debug=True)` ativam o Werkzeug debugger e o auto-reloader.
Impacto: Em qualquer ambiente exposto, uma exceção exibe um console interativo Python na resposta — RCE completo.
Recomendação: Controlar via variável de ambiente; produção sempre com DEBUG=False.

### [HIGH] God Module
Arquivo: models.py:1-315
Descrição: Um único arquivo de 315 linhas concentra acesso a dados, lógica de negócio (cálculo de total/desconto, validação de estoque), regras cross-entity e formatação de dicts para 4 domínios distintos (produtos, usuários, pedidos, itens).
Impacto: Mudanças em qualquer domínio afetam o arquivo inteiro; impossível testar uma entidade isoladamente; alto risco de regressões.
Recomendação: Quebrar em models/produto.py, models/usuario.py, models/pedido.py (apenas leitura/escrita) e mover workflows para controllers/.

### [HIGH] Lógica de Negócio na Camada de Dados
Arquivo: models.py:133-169 (criar_pedido), models.py:235-273 (relatorio_vendas)
Descrição: criar_pedido executa workflow multi-step (valida produtos, checa estoque, calcula total, cria pedido, registra itens, decrementa estoque) dentro do "model"; relatorio_vendas decide regras de desconto baseadas em faturamento.
Impacto: Lógica de negócio acoplada a SQL — impossível reusar sem o banco; testes exigem fixture completa.
Recomendação: Models só fazem CRUD da própria tabela; mover workflows para controllers/pedido_controller.py e controllers/relatorio_controller.py.

### [HIGH] Lógica de Negócio no Controller
Arquivo: controllers.py:188-220 (criar_pedido), controllers.py:237-255 (atualizar_status_pedido)
Descrição: O controller criar_pedido faz validação, chama o model que faz tudo e depois dispara "notificações" via print; atualizar_status_pedido mistura validação de domínio com side-effects de notificação.
Impacto: Side-effects (email/sms/push) presos ao handler HTTP, sem como invocar a partir de outro contexto (jobs, CLI).
Recomendação: Route faz parse → controller orquestra → model persiste → notification_service envia. Manter o handler abaixo de ~15 linhas.

### [HIGH] Acoplamento Forte — sem Injeção de Dependência
Arquivo: models.py:1, controllers.py:2-3
Descrição: Todos os módulos importam `from database import get_db` no topo e usam o singleton global; não há ponto de injeção para testes.
Impacto: Impossível substituir DB por fake em testes unitários; mudança de engine (ex.: PostgreSQL) exige reescrever todos os módulos.
Recomendação: Receber `db` como parâmetro (ou instanciar repositórios no composition root passando a conexão).

### [HIGH] Estado Global Mutável entre Requisições
Arquivo: database.py:4-10
Descrição: `db_connection = None` é variável global mutável compartilhada por todas as requisições; usa `check_same_thread=False`, desligando a proteção do sqlite3.
Impacto: Sob concorrência, cursores podem ser intercalados; transação aberta em um handler pode contaminar outro request.
Recomendação: Conexão por request (Flask `g.db`) ou pool gerenciado; remover `check_same_thread=False`.

### [HIGH] Política de CORS Aberta
Arquivo: app.py:9
Descrição: `CORS(app)` sem argumentos habilita Access-Control-Allow-Origin: * para todas as rotas.
Impacto: Browsers de qualquer origem podem invocar endpoints (incluindo futuros autenticados); ataques cross-origin facilitados.
Recomendação: Allowlist explícita lida de configuração: `CORS(app, origins=settings.CORS_ORIGINS)`.

### [HIGH] Autenticação Ausente em Endpoints Sensíveis
Arquivo: app.py:11-30, app.py:47, app.py:59
Descrição: Nenhuma rota exige autenticação — inclui /usuarios (CRUD), /pedidos (criar/listar todos), /relatorios/vendas e os endpoints /admin/*. GET /usuarios retorna o campo `senha` em claro.
Impacto: Qualquer cliente extrai todos os usuários e suas senhas, lista todos os pedidos e executa operações destrutivas.
Recomendação: Middleware/decorator de autenticação (JWT ou sessão); autorização por role para endpoints /admin/*.

### [MEDIUM] Queries N+1
Arquivo: models.py:171-201 (get_pedidos_usuario), models.py:203-233 (get_todos_pedidos)
Descrição: Para cada pedido faz SELECT em itens_pedido e, para cada item, faz SELECT em produtos para resolver o nome. Total: 1 + N + N×M round-trips.
Impacto: Latência cresce linearmente com o volume; em 1.000 pedidos × 5 itens, ~6.001 queries em vez de 1-3.
Recomendação: Substituir por JOIN único: `SELECT p.*, ip.*, pr.nome FROM pedidos p LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id LEFT JOIN produtos pr ON pr.id = ip.produto_id`.

### [MEDIUM] Validação de Input Ausente na Fronteira
Arquivo: controllers.py:146-165 (criar_usuario), controllers.py:167-186 (login), controllers.py:188-220 (criar_pedido), controllers.py:237-255 (atualizar_status_pedido)
Descrição: criar_usuario aceita qualquer string como email e qualquer senha; login não valida formato; criar_pedido não valida tipos/valores em `itens[].quantidade`; status válidos são lista hardcoded duplicada do model.
Impacto: Erros 500 em entradas malformadas; possível inconsistência (quantidade negativa, email inválido criando usuário não recuperável).
Recomendação: Validação por schema (pydantic/marshmallow) em routes/; retornar 400 com erro estruturado.

### [MEDIUM] Campos Sensíveis Expostos nas Respostas
Arquivo: models.py:79-86 (get_todos_usuarios), models.py:95-102 (get_usuario_por_id)
Descrição: A serialização de usuário inclui o campo `senha`; GET /usuarios retorna senhas em claro de todos os usuários.
Impacto: Vazamento direto de credenciais por uma API pública (combinado com auth ausente, ainda mais grave).
Recomendação: Serializer dedicado (DTO) que nunca inclui `senha`/`password_hash`; aplicar em todos os endpoints.

### [MEDIUM] Duplicação de Código (try/except, row→dict)
Arquivo: controllers.py (try/except em ~14 handlers), models.py:4-22, 30-41, 302-313 (mapeamento idêntico de produto), models.py:78-86, 94-102 (mapeamento idêntico de usuário)
Descrição: O wrapper `try: ... except Exception as e: return jsonify({"erro": str(e)}), 500` aparece em quase todos os handlers; o mapeamento manual de row → dict repete-se 3× para produto e 2× para usuário.
Impacto: Correções de bug não propagam; ruído visual obscurece a lógica real.
Recomendação: errorhandler central no Flask; funções `produto_from_row(row)` / `usuario_from_row(row)`.

### [MEDIUM] Logging via print / Notificações disfarçadas de print
Arquivo: app.py:56, 83-86; controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250
Descrição: Toda a observabilidade é via `print(...)`. O "envio" de email/sms/push é feito com `print("ENVIANDO EMAIL: ...")` — não há módulo de notificação real.
Impacto: Sem níveis de log, sem rotação, sem correlation-id; lógica de notificação inexistente disfarçada como log.
Recomendação: Trocar por `logging.getLogger(__name__)` configurado em config/; extrair um services/notification.py mesmo que stub.

### [LOW] Magic Numbers e Listas de Domínio Hardcoded
Arquivo: models.py:257-262 (limiares 10000/5000/1000 e taxas 0.1/0.05/0.02), controllers.py:52 (categorias hardcoded), controllers.py:242 (status válidos hardcoded)
Descrição: Regras de desconto, lista de categorias e lista de status válidos estão embarcadas como literais espalhadas pelo código.
Impacto: Mudança em regra de negócio exige caçar literais; risco de divergência (categorias_validas no controller difere de constraints no model).
Recomendação: Centralizar em config/constants.py (CATEGORIAS_VALIDAS, STATUS_PEDIDO_VALIDOS, REGRAS_DESCONTO).

### [LOW] Concatenação de Strings para Mensagens
Arquivo: controllers.py:8, 11, 54, 57, 61, 106, 143, 145, 161, 179, 182, 208-210, 219, 248, 250; models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 143, 145, 150, 159-160, 165, 174, 192, 224, 280, 289-297
Descrição: Mensagens e strings montadas com `"texto " + str(x)` (Python 3.6+ tem f-strings).
Impacto: Legibilidade; em algumas localizações o mesmo padrão é exatamente o que habilita as SQLi.
Recomendação: Padronizar f-strings para mensagens; para SQL, usar exclusivamente placeholders.

### [LOW] Nomenclatura Genérica / Sombreamento de builtins
Arquivo: controllers.py:14, 64, 98, 138 (parâmetro `id` sombreia builtin), controllers.py:26, 66, 148, 170, 239 (`dados`)
Descrição: Uso de `id` como nome de parâmetro (sombreia o builtin); variável `dados` genérica em quase todos os handlers.
Impacto: Legibilidade; possíveis bugs sutis quando o `id()` builtin é necessário.
Recomendação: Renomear para `produto_id` / `usuario_id` / `payload`.

================================
Total: 23 findings
================================

Fase 2 concluída. Prosseguir com a refatoração (Fase 3)? [s/n]
