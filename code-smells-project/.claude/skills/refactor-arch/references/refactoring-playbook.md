# Playbook de Refatoração (Fase 3)

Cada entrada abaixo mapeia um ou mais anti-patterns do catálogo para uma transformação concreta, com código **antes** e **depois**. Pegue o sabor da linguagem que combina com o projeto; o princípio é o mesmo entre stacks.

Quando múltiplos findings têm a mesma causa raiz, aplicar uma transformação que resolva todos juntos.

---

## 1. Credenciais Hardcoded → Módulo de config + variáveis de ambiente

**Resolve:** Credenciais Hardcoded, CORS aberto com origens hardcoded.

### Antes (Python/Flask)
```python
# app.py
app = Flask(__name__)
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
DB_PATH = "/tmp/store.db"
CORS(app, origins="*")
```

### Depois
```python
# config/settings.py
import os

class Settings:
    SECRET_KEY = os.environ["SECRET_KEY"]
    DB_PATH = os.environ.get("DB_PATH", "store.db")
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
    ENV = os.environ.get("ENV", "development")

settings = Settings()
```

```python
# app.py
from config.settings import settings
app = Flask(__name__)
app.config["SECRET_KEY"] = settings.SECRET_KEY
CORS(app, origins=settings.CORS_ORIGINS)
```

Criar um `.env.example` documentando as variáveis exigidas. Adicionar `.env` ao `.gitignore` (sem remover entradas existentes).

---

## 2. SQL Injection → Queries parametrizadas

**Resolve:** SQL Injection.

### Antes (Python/sqlite3)
```python
def buscar_usuario(nome):
    cursor.execute(f"SELECT * FROM usuarios WHERE nome = '{nome}'")
    return cursor.fetchone()
```

### Depois
```python
def buscar_usuario(nome):
    cursor.execute("SELECT * FROM usuarios WHERE nome = ?", (nome,))
    return cursor.fetchone()
```

### Antes (Node.js / mysql2)
```js
db.query(`SELECT * FROM users WHERE id = ${userId}`);
```

### Depois
```js
db.query("SELECT * FROM users WHERE id = ?", [userId]);
```

Aplicar em todo ponto onde input do usuário toca uma query, inclusive `ORDER BY` (que não pode ser parametrizado — validar contra allowlist).

---

## 3. Senhas em Texto Puro → Hash com bcrypt/argon2

**Resolve:** Armazenamento de Senha em Texto Puro.

### Antes
```python
def cadastrar(email, senha):
    db.execute("INSERT INTO usuarios (email, senha) VALUES (?, ?)", (email, senha))
```

### Depois
```python
import bcrypt

def cadastrar(email, senha):
    hash_senha = bcrypt.hashpw(senha.encode(), bcrypt.gensalt())
    db.execute("INSERT INTO usuarios (email, password_hash) VALUES (?, ?)", (email, hash_senha))

def verificar(email, senha):
    row = db.execute("SELECT password_hash FROM usuarios WHERE email = ?", (email,)).fetchone()
    return row and bcrypt.checkpw(senha.encode(), row["password_hash"])
```

Se o schema existente tem coluna `senha`, renomeá-la para `password_hash` e migrar dados existentes (ou marcar como "stale" e forçar reset no próximo login).

---

## 4. God Module → Quebrar por domínio em Models + Controllers

**Resolve:** God Class / God Module, Lógica de Negócio em Controllers.

### Antes
Um único `models.py` (ou `AppManager.js`) com rotas, queries e formatação para produtos, pedidos e usuários.

### Depois
```
models/
  produto.py        # classe Produto + métodos de DB específicos de produto
  pedido.py
  usuario.py
controllers/
  produto_controller.py  # casos de uso (criar, listar, atualizar, deletar)
  pedido_controller.py
  usuario_controller.py
routes/
  produto_routes.py      # @route → método do controller
  pedido_routes.py
  usuario_routes.py
```

Processo por entidade:
1. Identificar todas as funções do god module que tocam uma mesma entidade.
2. Mover funções de acesso a dados para `models/<entidade>.py` como classmethods/staticmethods.
3. Mover lógica multi-step para `controllers/<entidade>_controller.py`.
4. Mover declarações de rota para `routes/<entidade>_routes.py` e reduzir cada handler a: parse → chama controller → retorna.
5. Atualizar imports no entry point.

---

## 5. Lógica de Negócio no Handler → Controller

**Resolve:** Lógica de Negócio em Controllers / Rotas.

### Antes (Express)
```js
app.post("/orders", async (req, res) => {
  const { userId, items } = req.body;
  let total = 0;
  for (const i of items) {
    const p = await db.query("SELECT price FROM products WHERE id = ?", [i.productId]);
    total += p[0].price * i.qty;
  }
  if (total > 1000) total = total * 0.9;
  const result = await db.query("INSERT INTO orders (user_id, total) VALUES (?, ?)", [userId, total]);
  await sendConfirmationEmail(userId, total);
  res.status(201).json({ id: result.insertId, total });
});
```

### Depois
```js
// controllers/orders.controller.js
export async function createOrder({ userId, items }, { orderModel, productModel, emailer }) {
  const total = await productModel.calculateTotal(items);
  const discounted = total > 1000 ? total * 0.9 : total;
  const order = await orderModel.create({ userId, total: discounted });
  await emailer.sendConfirmation(userId, discounted);
  return order;
}

// routes/orders.routes.js
router.post("/orders", async (req, res, next) => {
  try {
    const order = await createOrder(req.body, deps);
    res.status(201).json(order);
  } catch (e) { next(e); }
});
```

---

## 6. Acoplamento Forte → Injeção de Dependência no composition root

**Resolve:** Acoplamento Forte, Estado Global Mutável.

### Antes
```js
// controllers/user.js
const db = require("../db");
function getUser(id) { return db.query("..."); }
```

### Depois
```js
// controllers/user.js
export function makeUserController({ db }) {
  return {
    getUser(id) { return db.query("..."); },
  };
}

// app.js (composition root)
const db = require("./db");
const userController = makeUserController({ db });
app.locals.userController = userController;
```

Em Python, receber dependências como argumentos do construtor (`class UserController: def __init__(self, db):`).

---

## 7. Tratamento de Erro Ausente → Middleware central

**Resolve:** Tratamento de Erro Ausente ou Silenciado.

### Antes (Express)
```js
app.get("/products/:id", async (req, res) => {
  try {
    const p = await db.query("...");
    res.json(p);
  } catch (e) {
    res.status(500).json({ error: e.message });  // repetido em toda rota
  }
});
```

### Depois
```js
// middlewares/errorHandler.js
class HttpError extends Error {
  constructor(status, message) { super(message); this.status = status; }
}

export function errorHandler(err, req, res, next) {
  const status = err.status || 500;
  if (status >= 500) console.error(err);
  res.status(status).json({ error: err.message });
}

// app.js — deve ser registrado DEPOIS das rotas
app.use(errorHandler);
```

Em Flask:
```python
# middlewares/error_handler.py
def register_error_handlers(app):
    @app.errorhandler(HttpError)
    def _http(e):
        return jsonify(error=str(e)), e.status

    @app.errorhandler(Exception)
    def _unexpected(e):
        app.logger.exception(e)
        return jsonify(error="erro interno"), 500
```

Aí toda rota pode apenas dar `raise HttpError(404, "não encontrado")`.

---

## 8. Query N+1 → Query batched única

**Resolve:** Query N+1.

### Antes
```python
pedidos = db.query("SELECT * FROM pedidos WHERE usuario_id = ?", (usuario_id,))
for p in pedidos:
    p["itens"] = db.query("SELECT * FROM itens_pedido WHERE pedido_id = ?", (p["id"],))
```

### Depois
```python
pedidos = db.query("SELECT * FROM pedidos WHERE usuario_id = ?", (usuario_id,))
pedido_ids = [p["id"] for p in pedidos]
placeholders = ",".join("?" * len(pedido_ids))
itens = db.query(f"SELECT * FROM itens_pedido WHERE pedido_id IN ({placeholders})", pedido_ids)
itens_por_pedido = {}
for it in itens:
    itens_por_pedido.setdefault(it["pedido_id"], []).append(it)
for p in pedidos:
    p["itens"] = itens_por_pedido.get(p["id"], [])
```

Com ORM, preferir `joinedload` / `select_related` / `.populate()`.

---

## 9. Validação de Input Ausente → Validação por schema na fronteira

**Resolve:** Validação de Input Ausente.

### Antes (Flask)
```python
@app.route("/usuarios", methods=["POST"])
def criar_usuario():
    dados = request.get_json()
    return usuario_controller.criar(dados["email"], dados["senha"])
```

### Depois (estilo pydantic, ou marshmallow)
```python
# routes/usuario_routes.py
from pydantic import BaseModel, EmailStr, constr

class CriarUsuarioDTO(BaseModel):
    email: EmailStr
    senha: constr(min_length=8)

@app.route("/usuarios", methods=["POST"])
def criar_usuario():
    dto = CriarUsuarioDTO(**request.get_json())
    return usuario_controller.criar(dto.email, dto.senha)
```

Em Express, usar `zod` ou `express-validator`. Rejeitar com 400 + corpo de erro estruturado em caso de falha (tratado centralmente pelo error middleware).

---

## 10. API Deprecated → Substituto moderno

**Resolve:** Uso de API Deprecated.

Substituir cada ocorrência pelo equivalente moderno:

| Deprecated | Moderno |
|---|---|
| `new Buffer(x)` | `Buffer.from(x)` (ou `Buffer.alloc(n)` para tamanho) |
| `crypto.createCipher(algo, password)` | `crypto.createCipheriv(algo, key, iv)` com IV apropriado |
| `url.parse(str)` | `new URL(str)` |
| pacote `body-parser` | `app.use(express.json())` / `express.urlencoded({extended:true})` |
| `req.param("x")` | `req.params.x` / `req.body.x` / `req.query.x` |
| `collection.update(filter, update)` | `collection.updateOne(...)` / `updateMany(...)` |
| `flask.json.dumps` (removido na 2.3) | `import json; json.dumps(...)` |
| `werkzeug.security.safe_str_cmp` | `hmac.compare_digest` |
| `before_first_request` (deprecated Flask) | App factory com init explícito |
| `Query.get(id)` (SQLAlchemy legado) | `session.get(Model, id)` |
| `request` (pacote npm) | `node-fetch`, `axios` ou `fetch` built-in |

Varrer a codebase com grep por cada símbolo deprecated; substituir e re-testar.

---

## 11. Estado Global Mutável → Estado por requisição no banco

**Resolve:** Estado Global Mutável entre Requisições.

### Antes
```python
# cache no nível do módulo compartilhado por todas as requisições
cart_items = []

@app.route("/cart/add", methods=["POST"])
def add():
    cart_items.append(request.json)
    return jsonify(cart_items)
```

### Depois
- Persistir estado do carrinho no banco indexado por `usuario_id` / id de sessão.
- Buscar estado por requisição, mutar, persistir, retornar.

---

## 12. Magic Numbers → Constantes nomeadas

**Resolve:** Magic Numbers.

### Antes
```python
if usuario.tipo == 1:
    desconto = preco * 0.13
```

### Depois
```python
# constants.py (ou dentro do módulo do model)
class Tipo:
    ADMIN = 1
    CLIENTE = 2

TAXA_VAT = 0.13

if usuario.tipo == Tipo.ADMIN:
    desconto = preco * TAXA_VAT
```

---

## Ordem das operações (plano da Fase 3)

Ao aplicar transformações num projeto real, seguir esta ordem para não quebrar nada no meio do caminho:

1. **Montar a nova árvore** (`models/`, `routes/`, `controllers/`, `config/`, `middlewares/`). Arquivos vazios / `__init__.py`.
2. **Extrair config** (transformação 1) — segredos e strings de conexão fora do código-fonte.
3. **Quebrar o god module** (transformação 4) uma entidade por vez. Após cada entidade, verificar que o app ainda sobe e que os endpoints dessa entidade ainda respondem.
4. **Mover lógica de negócio das rotas** (transformação 5).
5. **Aplicar correções de segurança** (SQLi → 2, senhas em claro → 3).
6. **Centralizar tratamento de erro** (transformação 7).
7. **Adicionar validação na fronteira** (transformação 9).
8. **Varrer APIs deprecated** (transformação 10).
9. **Performance e polimento** (N+1 → 8, magic numbers → 12).
10. **Validar**: boot + smoke test dos endpoints. Reexaminar mentalmente a lógica da Fase 2 — todo finding deve estar resolvido ou explicitamente adiado.

Cada passo deve deixar o app em estado executável. Se não der para concluir um passo no escopo de um commit, terminar antes de começar o próximo.
