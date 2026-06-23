# Catálogo de Anti-Patterns (Fase 2)

Para cada arquivo-fonte, percorrer este catálogo de cima para baixo e registrar cada ocorrência como um finding. Cada entrada traz:

- **Severidade** — uma entre CRITICAL / HIGH / MEDIUM / LOW
- **Sinais de detecção** — coisas concretas para grepar ou casar por padrão
- **Por que importa** — para redigir um Impacto sensato no relatório
- **Recomendação base** — o que o relatório deve sugerir

Quando um mesmo arquivo viola múltiplos padrões, registrar cada um como um finding separado.

---

## Severidade CRITICAL

### 1. God Class / God Module
**Sinais de detecção:**
- Um único arquivo-fonte com > ~200 linhas misturando: definições de rota + lógica de negócio + acesso a banco + validação + formatação.
- Uma classe com > 10 métodos públicos cobrindo responsabilidades não relacionadas.
- Imports cobrem persistência, HTTP, formatação e regras de domínio no mesmo arquivo.

**Por que importa:** impossível testar em isolamento; qualquer mudança tem raio de explosão grande.

**Recomendação base:** dividir por domínio em models/, controllers/ e (opcionalmente) services/.

---

### 2. Credenciais / Segredos Hardcoded
**Sinais de detecção:**
- Atribuições do tipo `SECRET_KEY = "..."`, `API_KEY = "..."`, `password = "..."`, `JWT_SECRET = "..."` com string literal (não `os.environ.get(...)` / `process.env.X`).
- Strings de conexão com senha embutida: `"postgres://user:pass@host"`, `"mongodb://root:root@..."`.
- Tokens no código: `Bearer xxxxxx`.

**Por que importa:** segredos vão para o histórico Git, ficam visíveis a qualquer pessoa com acesso de leitura e a rotação após vazamento é dolorosa.

**Recomendação base:** mover para variáveis de ambiente, carregadas por um módulo de config; falhar rápido em produção se ausente.

---

### 3. SQL Injection
**Sinais de detecção:**
- Concatenação de string ou f-string dentro de SQL: `f"SELECT * FROM users WHERE id = {user_id}"`, `"SELECT ... WHERE name = '" + name + "'"`.
- Template-literal de SQL em Node: `` `SELECT * FROM x WHERE y = ${value}` ``.
- `cursor.execute(query)` com `query` construída por interpolação de string a partir de input do usuário.

**Por que importa:** qualquer cliente pode rodar SQL arbitrário; comprometimento total do banco.

**Recomendação base:** usar queries parametrizadas / bindings do ORM (`cursor.execute(sql, (param,))`, placeholders `?`, `db.query(sql, [param])`).

---

### 4. Armazenamento de Senha em Texto Puro / Hash Fraco
**Sinais de detecção:**
- Inserir campo `password` com valor cru na tabela de usuários.
- `md5(password)` ou `sha1(password)` sem salt para hash de senha.
- Comparar `user.password == provided_password` direto.

**Por que importa:** qualquer dump do banco expõe todos os usuários; rainbow tables quebram hashes fracos imediatamente.

**Recomendação base:** usar bcrypt / argon2 / scrypt com salt por usuário; nunca logar ou retornar campos de senha.

---

### 5. CORS Aberto / Origin `*` em produção
**Sinais de detecção:**
- `CORS(app, origins="*")` / `Access-Control-Allow-Origin: *` combinado com credenciais.
- `app.use(cors())` sem allowlist.

**Por que importa:** habilita ataques equivalentes a CSRF quando credenciais são enviadas entre origens.

**Recomendação base:** allowlist explícita de origens vinda da config.

---

## Severidade HIGH

### 6. Lógica de Negócio em Controllers / Rotas
**Sinais de detecção:**
- Handlers de rota contêm cálculos de preço, workflows multi-step, batching ou mutações transacionais com mais de ~15 linhas.
- Validação, escrita no banco, side-effects (email, webhook) e formatação de resposta moram todos dentro de uma função de rota.

**Por que importa:** a lógica não pode ser reusada nem testada sem subir a camada HTTP.

**Recomendação base:** mover lógica para módulo controller (ou service); a rota deve orquestrar: parse → chama controller → retorna.

---

### 7. Acoplamento Forte — sem Injeção de Dependência
**Sinais de detecção:**
- Módulos importam um cliente de banco concreto no nível do módulo e chamam direto (`import db; db.query(...)`).
- Construtores instanciam seus próprios colaboradores (`this.repo = new UserRepo()`).
- Não há como substituir o banco por um fake nos testes.

**Por que importa:** intestável; qualquer mudança de infra se espalha por todos os módulos que importaram o cliente.

**Recomendação base:** passar dependências como argumentos de funções/construtores; conectar uma única vez no composition root (entry point).

---

### 8. Estado Global Mutável entre Requisições
**Sinais de detecção:**
- Contêineres mutáveis no nível do módulo (listas/dicts) que handlers fazem append: `users_cache = []` e então `users_cache.append(...)` num handler.
- Contadores globais incrementados sem lock.
- Singletons guardando estado por usuário.

**Por que importa:** race conditions sob concorrência; vazamento de estado entre requisições/tenants.

**Recomendação base:** manter estado no banco ou em contexto por requisição; passar estado explicitamente.

---

### 9. Tratamento de Erro Ausente ou Silenciado
**Sinais de detecção:**
- `try: ... except: pass`, `try { ... } catch(e) {}`.
- Sem handler global de erro — exceções chegam ao default do framework e devolvem stack trace HTML em APIs JSON.
- Erros de banco convertidos em `200 OK` com body `{"error": ...}` (contrato inconsistente).

**Por que importa:** falhas silenciosas, contratos de erro inconsistentes, stack traces vazando em produção.

**Recomendação base:** middleware central de tratamento de erro mapeando exceções para respostas HTTP tipadas; deixar erros inesperados subirem para um único handler.

---

### 10. Autenticação / Autorização Ausente em Rotas Sensíveis
**Sinais de detecção:**
- Endpoints administrativos (`/users`, `/users/<id>`, `/admin/*`, `DELETE /...`) sem decorator/middleware de auth.
- Endpoints que retornam hashes de senha ou PII sensível sem checagem de autorização.

**Por que importa:** acesso não autorizado a dados ou operações destrutivas.

**Recomendação base:** middleware de autenticação + autorização por rota; nunca retornar campos de senha.

---

## Severidade MEDIUM

### 11. Query N+1
**Sinais de detecção:**
- `for x in list: db.query("SELECT ... WHERE id = ?", x.id)`.
- Um loop sobre resultados que chama um helper de fetch por item.

**Por que importa:** round-trips lineares dominam latência conforme o volume cresce.

**Recomendação base:** query única com `WHERE id IN (...)` ou ORM `.options(joinedload(...))` / `.include`.

---

### 12. Validação de Input Ausente
**Sinais de detecção:**
- Handlers lendo `request.json["field"]` sem checar tipo, presença, comprimento ou faixa.
- Sem schema de validação (pydantic, marshmallow, zod, joi, express-validator) em uso.

**Por que importa:** 500s em input malformado, DoS fácil, perda de integridade.

**Recomendação base:** validar na fronteira com schema; retornar 400 com body de erro estruturado.

---

### 13. Duplicação de Código
**Sinais de detecção:**
- Os mesmos ~5+ linhas aparecendo em 3+ lugares (conectar no banco, envelopar erro, formatar resposta, decodar JWT).

**Por que importa:** divergência entre cópias; correções de bug esquecem cópias.

**Recomendação base:** extrair helper / middleware / decorator.

---

### 14. Uso de APIs Deprecated
Atravessa categorias: detectar APIs obsoletas e recomendar o equivalente moderno.

**Python / Flask:**
- `flask.json.dumps`, `flask.json.loads` (removidos no Flask 2.3) → usar `import json` ou `flask.json.provider`.
- `request.is_xhr` (removido) → checar headers explicitamente.
- `before_first_request` (deprecated no 2.3) → init via app factory.
- `flask_script` (sem manutenção) → `flask --app ... run` / `click`.
- `werkzeug.security.safe_str_cmp` (removido) → `hmac.compare_digest`.

**Python / SQLAlchemy 2.x:**
- `Query.get()` (legado) → `session.get(Model, id)`.
- Autocommit implícito em engines → `with engine.begin()` explícito.

**Node.js:**
- `new Buffer(x)` (deprecated) → `Buffer.from(x)` / `Buffer.alloc(n)`.
- `crypto.createCipher` / `createDecipher` → `createCipheriv` / `createDecipheriv`.
- `url.parse` (legado) → `new URL(...)` (WHATWG URL).
- `fs.exists` → `fs.existsSync` / `fs.promises.access`.
- pacote `request` (deprecated) → `node:fetch`, `axios`, `undici`.

**Express:**
- pacote separado `body-parser` → built-in `express.json()` / `express.urlencoded()` desde Express 4.16.
- `req.param()` (removido) → `req.params.x` / `req.body.x` / `req.query.x`.

**Driver MongoDB:**
- `collection.update()` / `remove()` → `updateOne` / `updateMany` / `deleteOne` / `deleteMany`.

**Sinal geral:** qualquer deprecation warning que apareceria em runtime; qualquer símbolo de framework marcado como deprecated na major atual.

**Por que importa:** será removido na próxima major; correções de segurança param de chegar; ajuda da comunidade seca.

**Recomendação base:** trocar pela API moderna acima.

---

### 15. Logging Inconsistente / Inadequado
**Sinais de detecção:**
- `print(...)` / `console.log(...)` usado como log de produção.
- Sem correlação por request-id; sem distinção de nível (info / warn / error).
- Campos sensíveis logados (senhas, tokens, bodies inteiros).

**Por que importa:** invisibilidade em produção; possível vazamento de PII para logs.

**Recomendação base:** usar logger estruturado (`logging`, `pino`, `winston`); nunca logar segredos.

---

## Severidade LOW

### 16. Magic Numbers / Strings
**Sinais de detecção:**
- Literais numéricos embarcados na lógica de negócio: `if user.role == 1`, `price * 0.13`, `if days > 30`.
- Strings de status repetidas: `"approved"`, `"pending"` espalhadas entre arquivos.

**Recomendação base:** constantes nomeadas ou enums em um módulo `constants/`.

---

### 17. Nomenclatura Ruim
**Sinais de detecção:**
- Identificadores de uma letra ou genéricos em escopo não-trivial: `data`, `tmp`, `aux`, `x`, `obj`, `info`.
- Funções nomeadas `process()`, `handle()`, `do_stuff()`.

**Recomendação base:** renomear para algo que revele a intenção.

---

### 18. Código Morto / Blocos Comentados
**Sinais de detecção:**
- Grandes blocos comentados de lógica antiga.
- Funções/imports com zero referências no projeto.

**Recomendação base:** deletar; o histórico Git preserva.

---

## Referência rápida de severidade

| Severidade | Usar quando... |
|---|---|
| **CRITICAL** | Falha de segurança, risco de perda de dados ou violação arquitetural que torna o sistema inviável. |
| **HIGH** | Forte violação de MVC/SOLID; testabilidade e manutenibilidade seriamente comprometidas. |
| **MEDIUM** | Padronização, duplicação, performance moderada ou validação ausente. |
| **LOW** | Legibilidade e higiene em pequena escala. |

Quando um sinal puder ser plausivelmente classificado em duas severidades, escolher a mais alta se tocar segurança/integridade de dados; caso contrário a mais baixa.
