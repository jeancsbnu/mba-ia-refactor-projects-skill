# Heurísticas de Análise do Projeto (Fase 1)

Use estas heurísticas para detectar a stack e a arquitetura atual. Seja determinístico — todo valor impresso no bloco da Fase 1 deve ser defendido por pelo menos um sinal observado no repositório.

---

## 1. Detecção de linguagem

Inspecionar o diretório de trabalho por estes sinais:

| Sinal | Linguagem |
|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, arquivos `*.py` | **Python** |
| `package.json`, `*.js`, `*.ts`, `*.mjs` | **Node.js** |
| `go.mod`, `*.go` | Go |
| `Gemfile`, `*.rb` | Ruby |
| `composer.json`, `*.php` | PHP |
| `pom.xml`, `build.gradle`, `*.java` | Java |
| `Cargo.toml`, `*.rs` | Rust |

Se múltiplos sinais aparecerem, a linguagem dominante é a com mais arquivos-fonte.

---

## 2. Detecção de framework + versão

### Python
- `flask` em `requirements.txt` ou `from flask import` no código → **Flask**.
  Versão: ler a versão pinada em `requirements.txt`; se livre, rodar `pip show flask` se disponível, senão declarar "desconhecida".
- `fastapi` → **FastAPI**.
- `django`, `manage.py`, `settings.py` → **Django**.
- `starlette` (sem FastAPI) → Starlette.

### Node.js
- `express` em `dependencies` no `package.json` → **Express**.
- `fastify` → Fastify.
- `@nestjs/core` → NestJS.
- `next` → Next.js (full-stack).
- `koa` → Koa.

Ler a versão do `package.json` (`dependencies.express`).

### Outros
- Spring Boot: `spring-boot-starter-*` no pom.xml.
- Rails: `rails` no Gemfile.
- Laravel: `laravel/framework` no composer.json.

---

## 3. Detecção de banco de dados

| Sinal | Banco |
|---|---|
| import `sqlite3`, arquivo `*.db` / `*.sqlite` | SQLite |
| `psycopg2`, `pg`, string `postgres://`/`postgresql://` | PostgreSQL |
| `mysql`, `mysql2`, `pymysql` | MySQL |
| `pymongo`, `mongoose`, `mongodb://` | MongoDB |
| `redis` | Redis (geralmente cache, não primário) |
| `sqlalchemy`, `prisma`, `sequelize`, `typeorm`, `mongoose` | ORM/ODM em uso |

### Extração de schema
- **SQLite**: grep por `CREATE TABLE` no código-fonte. Se houver `*.db` e o `sqlite3` CLI estiver disponível, rodar `sqlite3 caminho/do/arquivo.db ".schema"` para ler as tabelas.
- **Modelos ORM**: enumerar classes que estendem `db.Model` (SQLAlchemy), `Sequelize.Model`, `mongoose.Schema` ou têm decorador `@Entity`.
- **SQL puro**: grep por `INSERT INTO`, `SELECT ... FROM`, `CREATE TABLE` para reconstituir o schema implícito.

Listar as tabelas / coleções encontradas no bloco da Fase 1.

---

## 4. Inferência do domínio

Dois sinais complementares:

1. **Paths de rota**: enumerar todas as declarações de rota.
   - Flask: `@app.route("/...")`, `@blueprint.route("/...")`
   - Express: `app.get|post|put|delete|patch("/...", ...)`, `router.METHOD(...)`
   - FastAPI: `@app.get("/...")` etc.

2. **Nomes de model / tabela**: a partir da seção 3.

Cruzar os dois para escrever uma descrição de uma linha do domínio, por exemplo:
- Rotas `/produtos`, `/pedidos`, `/usuarios` + tabelas `produtos`, `pedidos`, `usuarios` → "API de E-commerce (produtos, pedidos, usuários)"
- Rotas `/tasks`, `/categories`, `/users` + tabelas `tasks`, `categories` → "API de Task Manager"
- Rotas `/courses`, `/enrollments`, `/checkout` → "API de LMS / checkout de e-commerce"

Mencionar o idioma dos termos de domínio (português / inglês / misto).

---

## 5. Classificação da arquitetura

Escolher um dos rótulos abaixo e justificar em uma linha:

- **Monolítica** — menos de ~5 arquivos-fonte, ou um arquivo concentra rotas + lógica de negócio + acesso a banco; nenhuma pasta `models/`, `controllers/`, `services/`.
- **Parcialmente organizada** — existe alguma estrutura (ex.: `routes/`, `services/`, `models/`) mas ao menos uma fronteira vaza (lógica de negócio em routes, SQL bruto em controllers, validação duplicada).
- **MVC** — pastas explícitas `models/`, `views/` ou `routes/`, `controllers/`, cada uma com módulos de responsabilidade única. Config e entry point isolados.

Na dúvida entre Monolítica e Parcialmente organizada, contar pastas que agrupam código por preocupação. ≥2 dessas pastas → Parcialmente organizada.

---

## 6. Contagem de arquivos-fonte

Contar arquivos no diretório de trabalho que casam com as extensões da linguagem do projeto, excluindo:
- Pastas de dependências (`node_modules`, `__pycache__`, `.venv`, `venv`, `dist`, `build`)
- Arquivos gerados (lockfiles, saída compilada)
- A própria pasta `.claude/` da skill
- A pasta `reports/`

Declarar a contagem exata no bloco da Fase 1.

---

## 7. Saída da Fase 1 (formato exato)

```
================================
FASE 1: ANÁLISE DO PROJETO
================================
Linguagem:     <ex.: Python 3.11>
Framework:     <ex.: Flask 3.1.1>
Dependências:  <lista separada por vírgula das deps relevantes>
Domínio:       <descrição em uma linha do domínio de negócio>
Arquitetura:   <Monolítica | Parcialmente organizada | MVC> — <motivo em uma linha>
Arquivos:      <N> arquivos analisados
Tabelas DB:    <lista separada por vírgula, ou "nenhuma detectada">
================================
```
